#!/usr/bin/env python3
"""Deterministic marginal- and total-risk-contribution engine for portfolio-risk-contribution-analyzer.

Reads a risk-contribution-input file (see validate_input.py), and for a portfolio's weights
and an approved covariance matrix computes the ex-ante portfolio risk and its Euler
decomposition:

    portfolio_variance   var_p   = w' * Sigma * w
    portfolio_risk       sigma_p = sqrt(var_p)
    marginal contribution MCR_i  = (Sigma * w)_i / sigma_p         # d sigma_p / d w_i
    total contribution    TRC_i  = w_i * MCR_i                     # component risk
    percent contribution  PCR_i  = TRC_i / sigma_p

By Euler's theorem for the (degree-1 homogeneous) volatility measure, sum(TRC_i) == sigma_p
and sum(PCR_i) == 1 exactly; these are the load-bearing tie-outs. Contributions are also
aggregated by a configured grouping dimension (e.g. sector). The computed portfolio risk is
reconciled to the approved risk engine's reported total, and — when a prior review is
supplied — per-position and total-risk changes are measured against a documented materiality
threshold. The model is reproducible from a hash of its numeric inputs.

IMPORTANT: This produces an *illustrative risk-contribution analysis* only. It never sets or
changes a risk limit, never mandates or recommends a trade, rebalance, or hedge, and never
gives investment advice. Methodology, weights, and covariance are documented inputs, not the
skill's judgment. See references/domain-rules.md.

Usage:
  python calculate_or_transform.py risk_input.json | --selftest
Prints the model JSON to stdout.
"""
from __future__ import annotations
import hashlib, json, math, sys
from pathlib import Path

ROUND = 6            # risk figures are small (order 0.1); keep 6 dp
TOL = 1e-4           # tie-out tolerance
DISCLAIMER = ("Illustrative risk-contribution analysis for analytical purposes only; not a "
              "risk limit, not a mandate to trade, rebalance, or hedge, and not investment "
              "advice. Risk contributions are conditional on the stated methodology, "
              "weights, and covariance inputs, which a qualified human and the approved risk "
              "engine must review.")


def _v(node):
    """Numeric value from a bare scalar or a {value, provenance, citation} dict."""
    if isinstance(node, dict):
        return float(node.get("value"))
    return float(node)


def _prov(node):
    return (node.get("provenance", "") if isinstance(node, dict) else "")


def _cite(node):
    return (node.get("citation", "") if isinstance(node, dict) else "")


def _compute(doc: dict) -> dict:
    positions = doc["positions"]
    pos_ids = [p["position_id"] for p in positions]
    weights = [_v(p["weight"]) for p in positions]
    n = len(positions)

    # --- covariance aligned to positions order ----------------------------------------
    cov = doc["covariance"]
    order = cov.get("order", pos_ids)
    matrix = cov["matrix"]
    idx = {pid: i for i, pid in enumerate(order)}
    # reorder rows/cols of matrix into positions order so w and Sigma align
    sigma_m = [[float(matrix[idx[a]][idx[b]]) for b in pos_ids] for a in pos_ids]

    # --- portfolio variance / risk ----------------------------------------------------
    sigma_w = [sum(sigma_m[i][j] * weights[j] for j in range(n)) for i in range(n)]
    var_p = sum(weights[i] * sigma_w[i] for i in range(n))
    var_guard_ok = var_p > 0.0
    sigma_p = math.sqrt(var_p) if var_guard_ok else 0.0

    # --- per-position contributions ---------------------------------------------------
    contributions = []
    for i, p in enumerate(positions):
        mcr = (sigma_w[i] / sigma_p) if var_guard_ok else 0.0
        trc = weights[i] * mcr
        pcr = (trc / sigma_p) if var_guard_ok else 0.0
        # per-position tie-out: TRC == w * MCR (exact by construction; recorded for audit)
        trc_ok = abs(trc - weights[i] * mcr) <= TOL
        contributions.append({
            "position_id": p["position_id"],
            "instrument_id": p.get("instrument_id"),
            "issuer": p.get("issuer"),
            "group": p.get(doc.get("grouping_dimension", "sector")),
            "weight": round(weights[i], ROUND),
            "mcr": round(mcr, ROUND),
            "trc": round(trc, ROUND),
            "pcr": round(pcr, ROUND),
            "trc_tieout_ok": trc_ok,
        })

    sum_trc = round(sum(c["trc"] for c in contributions), ROUND)
    sum_pcr = round(sum(c["pcr"] for c in contributions), ROUND)

    # --- grouping (sum of contributions by the configured dimension) ------------------
    gdim = doc.get("grouping_dimension", "sector")
    groups = {}
    for c in contributions:
        g = c["group"] if c["group"] is not None else "(unclassified)"
        gg = groups.setdefault(g, {"group": g, "trc": 0.0, "pcr": 0.0, "weight": 0.0, "positions": []})
        gg["trc"] += c["trc"]
        gg["pcr"] += c["pcr"]
        gg["weight"] += c["weight"]
        gg["positions"].append(c["position_id"])
    group_rows = []
    for g in sorted(groups):
        gg = groups[g]
        group_rows.append({"group": gg["group"], "dimension": gdim,
                           "weight": round(gg["weight"], ROUND),
                           "trc": round(gg["trc"], ROUND), "pcr": round(gg["pcr"], ROUND),
                           "positions": gg["positions"]})

    # --- reconciliation to the approved risk engine total -----------------------------
    ae = doc.get("approved_engine") or {}
    approved_total = _v(ae.get("total_risk")) if "total_risk" in ae else None
    tol_rel = float((doc.get("reconciliation") or {}).get("tolerance_rel", 0.01))
    computed_total = round(sigma_p, ROUND)
    reconciliation = None
    if approved_total is not None:
        abs_diff = round(computed_total - approved_total, ROUND)
        rel_diff = round(abs(abs_diff) / abs(approved_total), 8) if approved_total else None
        reconciled = (rel_diff is not None and rel_diff <= tol_rel)
        reconciliation = {
            "approved_engine_total": round(approved_total, ROUND),
            "computed_total": computed_total,
            "abs_diff": abs_diff,
            "rel_diff": rel_diff,
            "tolerance_rel": tol_rel,
            "reconciled": reconciled,
        }

    # --- material changes since prior review ------------------------------------------
    material_changes = None
    prior = doc.get("prior_review")
    if prior:
        m = doc.get("materiality") or {}
        pcr_thr = float(m.get("pcr_abs_threshold", 0.03))
        tot_thr = float(m.get("total_risk_rel_threshold", 0.05))
        prior_by = {q["position_id"]: q for q in prior.get("positions", [])}
        cur_by = {c["position_id"]: c for c in contributions}
        pos_changes = []
        for pid in sorted(set(prior_by) | set(cur_by)):
            cur = cur_by.get(pid)
            pr = prior_by.get(pid)
            cur_pcr = cur["pcr"] if cur else None
            pr_pcr = float(pr["pcr"]) if pr else None
            if cur_pcr is None:
                status, d_pcr = "removed", None
            elif pr_pcr is None:
                status, d_pcr = "added", None
            else:
                d_pcr = round(cur_pcr - pr_pcr, ROUND)
                status = "changed"
            material = (d_pcr is not None and abs(d_pcr) >= pcr_thr) or status in ("added", "removed")
            pos_changes.append({"position_id": pid, "status": status,
                                "prior_pcr": pr_pcr, "current_pcr": cur_pcr,
                                "delta_pcr": d_pcr, "material": material})
        prior_total = float(prior["total_risk"]) if "total_risk" in prior else None
        tot_abs = round(computed_total - prior_total, ROUND) if prior_total is not None else None
        tot_rel = (round(tot_abs / prior_total, 8) if prior_total else None) if prior_total is not None else None
        tot_material = tot_rel is not None and abs(tot_rel) >= tot_thr
        material_changes = {
            "prior_packet_id": prior.get("packet_id"),
            "prior_as_of": prior.get("as_of"),
            "pcr_abs_threshold": pcr_thr,
            "total_risk_rel_threshold": tot_thr,
            "total_risk_prior": prior_total,
            "total_risk_current": computed_total,
            "total_risk_delta_abs": tot_abs,
            "total_risk_delta_rel": tot_rel,
            "total_risk_material": tot_material,
            "position_changes": pos_changes,
            "material_position_ids": [p["position_id"] for p in pos_changes if p["material"]],
        }

    # --- assumptions register (provenance + citation for every input assumption) ------
    method = doc.get("methodology") or {}
    register = []
    for p in positions:
        node = p["weight"]
        register.append({"id": f"weight:{p['position_id']}", "scope": "portfolio-weight",
                         "value": _v(node), "provenance": _prov(node), "citation": _cite(node)})
    register.append({"id": "covariance:matrix", "scope": "risk-model",
                     "value": None, "provenance": _prov(cov), "citation": _cite(cov)})
    register.append({"id": "methodology", "scope": "methodology",
                     "value": method.get("version"), "provenance": _prov(method),
                     "citation": _cite(method)})
    if approved_total is not None:
        node = ae["total_risk"]
        register.append({"id": "approved_engine:total_risk", "scope": "reconciliation-anchor",
                         "value": _v(node), "provenance": _prov(node), "citation": _cite(node)})
    if prior:
        register.append({"id": "prior_review", "scope": "prior-baseline",
                         "value": prior.get("total_risk"),
                         "provenance": prior.get("provenance", "prior-approved-packet"),
                         "citation": prior.get("citation", f"packet:{prior.get('packet_id')}@{prior.get('as_of')}")})

    # --- model checks -----------------------------------------------------------------
    euler_ok = var_guard_ok and abs(sum_trc - computed_total) <= TOL
    pcr_sum_ok = var_guard_ok and abs(sum_pcr - 1.0) <= TOL
    group_trc_ok = var_guard_ok and abs(round(sum(g["trc"] for g in group_rows), ROUND) - computed_total) <= TOL
    group_pcr_ok = var_guard_ok and abs(round(sum(g["pcr"] for g in group_rows), ROUND) - 1.0) <= TOL
    per_pos_trc_ok = all(c["trc_tieout_ok"] for c in contributions)

    # --- reproducibility hash over the numeric assumptions ----------------------------
    hash_src = json.dumps({
        "positions": [{"id": p["position_id"], "w": _v(p["weight"])} for p in positions],
        "covariance": sigma_m,
        "methodology_version": method.get("version"),
        "grouping_dimension": gdim,
        "approved_total": approved_total,
        "tolerance_rel": tol_rel,
        "materiality": doc.get("materiality") or {},
        "prior_packet_id": (prior or {}).get("packet_id"),
    }, sort_keys=True)
    inputs_hash = hashlib.sha256(hash_src.encode("utf-8")).hexdigest()[:16]
    portfolio = str(doc["portfolio_id"]).replace("*", "")
    packet_id = f"riskcontrib-{portfolio}-{doc['as_of']}-{inputs_hash}"

    return {
        "packet_id": packet_id,
        "portfolio_id": doc["portfolio_id"],
        "as_of": doc["as_of"],
        "currency": doc.get("currency"),
        "units": doc.get("units"),
        "risk_measure": doc.get("risk_measure"),
        "config_version": doc.get("config_version"),
        "inputs_hash": inputs_hash,
        "methodology": {"name": method.get("name"), "version": method.get("version")},
        "grouping_dimension": gdim,
        "portfolio_variance": round(var_p, ROUND),
        "total_risk": computed_total,
        "var_guard_ok": var_guard_ok,
        "covariance": {"order": pos_ids, "matrix": sigma_m},
        "contributions": contributions,
        "sum_trc": sum_trc,
        "sum_pcr": sum_pcr,
        "group_contributions": group_rows,
        "reconciliation": reconciliation,
        "material_changes": material_changes,
        "assumptions_register": register,
        "model_checks": {
            "var_guard_ok": var_guard_ok,
            "euler_ok": euler_ok,
            "pcr_sum_ok": pcr_sum_ok,
            "group_trc_ok": group_trc_ok,
            "group_pcr_ok": group_pcr_ok,
            "per_position_trc_ok": per_pos_trc_ok,
            "reconciled": (reconciliation or {}).get("reconciled"),
        },
        "disclaimer": DISCLAIMER,
    }


SELFTEST_CHECKS = ("var_guard_ok", "euler_ok", "pcr_sum_ok", "group_trc_ok",
                   "group_pcr_ok", "per_position_trc_ok")


def compute(doc: dict) -> dict:
    """Fail on invalid inputs; bind the complete supplied evidence and configuration."""
    import runpy
    validator = runpy.run_path(str(Path(__file__).with_name("validate_input.py")))
    errors, warnings = validator["validate"](doc)
    if errors: raise ValueError("; ".join(errors))
    result = _compute(doc)
    integrity = runpy.run_path(str(Path(__file__).with_name("native_integrity.py")))
    digest = integrity["canonical_hash"](doc)
    result["inputs_hash"] = digest
    result["calculation_version"] = "phase1-1"
    result["analysis_status"] = "draft"
    result["professional_approval"] = "not_established_by_script"
    result["input_warnings"] = warnings
    for key in ("packet_id", "analysis_id", "forecast_id", "exposure_id", "run_id", "attribution_id"):
        if key in result:
            result["source_" + key] = result[key]
            result[key] = str(result[key]) + "-" + digest[:16]
            break
    return integrity["attach_source"](result, doc)


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "risk_input_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
        model = compute(doc)
        print(json.dumps(model, indent=2))
        checks = model["model_checks"]
        errs = [k for k in SELFTEST_CHECKS if not checks.get(k)]
        for k in errs:
            print("ERROR", f"model check failed: {k}")
        print(f"compute self-test: {len(errs)} error(s)")
        return 1 if errs else 0
    if argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
