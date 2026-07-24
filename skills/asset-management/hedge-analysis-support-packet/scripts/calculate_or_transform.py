#!/usr/bin/env python3
"""Deterministic hedge exposure/sensitivity engine for hedge-analysis-support-packet.

Reads a hedge-analysis input file (see validate_input.py), and for a HUMAN-DEFINED set of
candidate hedges computes — deterministically and first-order — the residual exposure per
risk factor, a gross-exposure coverage ratio, and the scenario P&L for the un-hedged
portfolio, each hedge alone, and each hedged portfolio, under analyst-supplied shocks. It
lays the candidate hedges out in a comparison table with an explicit limitations list, and
reconciles the portfolio gross sensitivity and scenario P&L to any stated approved-engine
totals. Every scenario/hedge carries its own tie-outs; every assumption carries provenance +
citation; the packet is reproducible from a hash of its inputs.

IMPORTANT: This produces an *illustrative support packet* only. It NEVER selects, recommends,
ranks, or endorses a hedge, NEVER decides whether to hedge, and NEVER authorizes or executes
a trade. Sensitivities, costs, and shocks are supplied inputs under an approved model, not
this engine's judgment. See references/domain-rules.md.

Sensitivity convention: each sensitivity `value` is the P&L, in the packet's reporting units,
for a +1 shock of the factor's standardized unit (e.g. +1bp for rates, +1pct for equity).
Scenario shocks are expressed in the same standardized factor units, so scenario P&L is the
linear sum over factors of sensitivity * shock.

Usage:
  python calculate_or_transform.py hedge_input.json   # prints the packet JSON to stdout
  python calculate_or_transform.py --selftest         # self-verifies over the bundled fixture
Self-test prints a line ending "N error(s)" and exits 0 (pass) / 1 (fail).
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

MONEY = 4        # money precision (reporting units)
COV = 6          # ratio precision
TOL = 0.01       # tie-out tolerance
RECON_ABS = 0.01     # reconciliation absolute tolerance
RECON_REL = 0.005    # reconciliation relative tolerance
DISCLAIMER = ("Illustrative hedge-analysis support packet for analytical purposes only. It "
              "calculates exposures, sensitivities, coverage, and scenario P&L for a "
              "human-defined set of candidate hedges under supplied, approved-model "
              "assumptions; it does not select, recommend, rank, or endorse any hedge, is "
              "not a recommendation to enter, adjust, or unwind any position, is not "
              "investment, legal, or tax advice, and does not authorize or execute any "
              "trade. Hedge selection and execution are human decisions; results are only "
              "as good as the stated assumptions, which a qualified human must review.")


def _v(node):
    """Numeric value from a bare scalar or a {value, provenance, citation} dict."""
    if isinstance(node, dict):
        return float(node.get("value"))
    return float(node)


def _prov(node):
    return (node.get("provenance", "") if isinstance(node, dict) else "")


def _cite(node):
    return (node.get("citation", "") if isinstance(node, dict) else "")


def _recon_tol(approved: float) -> float:
    return max(RECON_ABS, RECON_REL * abs(approved))


def compute(doc: dict) -> dict:
    factors = list((doc.get("risk_factors") or {}).keys())
    port = doc["portfolio"]
    p_sens = {f: _v(port["sensitivities"][f]) for f in port.get("sensitivities", {})}
    gross_p = round(sum(abs(p_sens.get(f, 0.0)) for f in factors), MONEY)

    scenarios = doc.get("scenarios") or []
    scen_defs = []
    for s in scenarios:
        shocks = {k: float(_v(v)) for k, v in (s.get("shocks") or {}).items()}
        scen_defs.append({"id": s["id"], "label": s.get("label", s["id"]), "shocks": shocks})

    def scen_pnl(sens: dict, shocks: dict) -> float:
        return round(sum(sens.get(f, 0.0) * shocks.get(f, 0.0) for f in factors), MONEY)

    # un-hedged portfolio scenario P&L (identical for every candidate)
    portfolio_scenario_pnl = {s["id"]: scen_pnl(p_sens, s["shocks"]) for s in scen_defs}

    comparison = []
    for h in doc.get("candidate_hedges") or []:
        h_sens = {f: _v(h["sensitivities"][f]) for f in h.get("sensitivities", {})}
        residual = {f: round(p_sens.get(f, 0.0) + h_sens.get(f, 0.0), MONEY) for f in factors}
        residual_gross = round(sum(abs(residual[f]) for f in factors), MONEY)
        coverage_overall = round((gross_p - residual_gross) / gross_p, COV) if gross_p else None
        coverage_by_factor = {}
        for f in factors:
            pf = p_sens.get(f, 0.0)
            coverage_by_factor[f] = round((abs(pf) - abs(residual[f])) / abs(pf), COV) if pf else None

        scen_pnl_rows = {}
        for s in scen_defs:
            pf_pnl = portfolio_scenario_pnl[s["id"]]
            h_pnl = scen_pnl(h_sens, s["shocks"])
            hedged = round(pf_pnl + h_pnl, MONEY)
            scen_pnl_rows[s["id"]] = {"portfolio": pf_pnl, "hedge": h_pnl, "hedged": hedged}

        # tie-outs (validate_output re-derives these independently)
        residual_ok = all(abs(residual[f] - (p_sens.get(f, 0.0) + h_sens.get(f, 0.0))) <= TOL
                          for f in factors)
        gross_ok = abs(residual_gross - sum(abs(residual[f]) for f in factors)) <= TOL
        cov_ok = (coverage_overall is None
                  or abs(coverage_overall - (gross_p - residual_gross) / gross_p) <= 1e-6)
        linear_ok = all(abs(r["hedged"] - (r["portfolio"] + r["hedge"])) <= TOL
                        for r in scen_pnl_rows.values())
        consistent_ok = all(
            abs(scen_pnl_rows[s["id"]]["hedged"] - scen_pnl(residual, s["shocks"])) <= TOL
            for s in scen_defs)

        cost = h.get("cost")
        comparison.append({
            "hedge_id": h["id"],
            "label": h.get("label", h["id"]),
            "sensitivities": h_sens,
            "cost": ({"value": _v(cost), "type": cost.get("type", "")} if isinstance(cost, dict)
                     else ({"value": float(cost)} if cost is not None else None)),
            "residual": residual,
            "residual_gross": residual_gross,
            "coverage_overall": coverage_overall,
            "coverage_by_factor": coverage_by_factor,
            "scenario_pnl": scen_pnl_rows,
            "tieouts": {"residual_ok": residual_ok, "gross_ok": gross_ok, "coverage_ok": cov_ok,
                        "scenario_linear_ok": linear_ok, "scenario_consistent_ok": consistent_ok},
        })

    # --- reconciliation to approved-engine totals (only when supplied) ------------------
    approved = port.get("approved_engine_totals") or {}
    recon = {"supplied": bool(approved)}
    all_recon_ok = True
    if "gross_sensitivity" in approved:
        a = float(_v(approved["gross_sensitivity"]))
        ok = abs(gross_p - a) <= _recon_tol(a)
        recon["gross"] = {"approved": a, "computed": gross_p, "tol": round(_recon_tol(a), MONEY), "ok": ok}
        all_recon_ok = all_recon_ok and ok
    recon_scn = {}
    for sid, av in (approved.get("scenarios") or {}).items():
        a = float(_v(av))
        c = portfolio_scenario_pnl.get(sid)
        ok = c is not None and abs(c - a) <= _recon_tol(a)
        recon_scn[sid] = {"approved": a, "computed": c, "tol": round(_recon_tol(a), MONEY), "ok": ok}
        all_recon_ok = all_recon_ok and ok
    if recon_scn:
        recon["scenarios"] = recon_scn
    recon["all_ok"] = all_recon_ok

    # --- assumptions register (provenance + citation for every input assumption) --------
    register = []
    model = doc.get("model") or {}
    register.append({"id": f"model:{model.get('id', '')}", "scope": "approved-model",
                     "value": model.get("version", ""), "provenance": _prov(model),
                     "citation": _cite(model)})
    for f in factors:
        node = doc["risk_factors"][f]
        register.append({"id": f"factor:{f}", "scope": "factor-definition",
                         "value": (node.get("unit") if isinstance(node, dict) else ""),
                         "provenance": _prov(node), "citation": _cite(node)})
    for f in port.get("sensitivities", {}):
        node = port["sensitivities"][f]
        register.append({"id": f"portfolio:{f}", "scope": "portfolio-sensitivity",
                         "value": _v(node), "provenance": _prov(node), "citation": _cite(node)})
    for h in doc.get("candidate_hedges") or []:
        for f in h.get("sensitivities", {}):
            node = h["sensitivities"][f]
            register.append({"id": f"hedge:{h['id']}:{f}", "scope": "hedge-sensitivity",
                             "value": _v(node), "provenance": _prov(node), "citation": _cite(node)})
        if isinstance(h.get("cost"), dict):
            register.append({"id": f"cost:{h['id']}", "scope": "hedge-cost", "value": _v(h["cost"]),
                             "provenance": _prov(h["cost"]), "citation": _cite(h["cost"])})
    for s in scenarios:
        register.append({"id": f"scenario:{s['id']}", "scope": "scenario-shock",
                         "value": json.dumps({k: float(_v(v)) for k, v in (s.get("shocks") or {}).items()},
                                             sort_keys=True),
                         "provenance": _prov(s), "citation": _cite(s)})

    # --- reproducibility hash over the numeric assumptions ------------------------------
    hash_src = json.dumps({
        "model": {"id": model.get("id"), "version": model.get("version"),
                  "effective_date": model.get("effective_date")},
        "factors": factors,
        "portfolio": {f: p_sens[f] for f in sorted(p_sens)},
        "hedges": {h["id"]: {f: _v(h["sensitivities"][f]) for f in sorted(h.get("sensitivities", {}))}
                   for h in doc.get("candidate_hedges") or []},
        "scenarios": {s["id"]: s["shocks"] for s in scen_defs},
    }, sort_keys=True)
    inputs_hash = hashlib.sha256(hash_src.encode("utf-8")).hexdigest()[:16]

    limitations = [
        "First-order (linear) sensitivities only: convexity, gamma, cross-gammas, and "
        "large-move non-linearity are not captured; results degrade for large shocks and "
        "for instruments with optionality.",
        f"Sensitivities and costs are supplied inputs under model "
        f"{model.get('id', '?')} {model.get('version', '?')} (effective "
        f"{model.get('effective_date', '?')}); this packet does not re-derive or price them.",
        "Scenario P&L is the sum of factor sensitivities times supplied shocks; it is not a "
        "full revaluation and excludes basis risk between a hedge instrument and the "
        "portfolio exposure it is intended to offset.",
        "Coverage ratios measure sensitivity offset only; they do not measure "
        "cost-effectiveness, liquidity, counterparty or collateral impact, tracking error, "
        "or path-dependent behaviour.",
        "Whether to hedge, and which of these candidate hedges to use, is a "
        "portfolio-manager / investment-committee judgment and is out of scope for this "
        "packet.",
    ]

    return {
        "packet_id": f"hedge-{str(doc.get('case_id', doc['portfolio']['id']))}-"
                     f"{doc['valuation_date']}-{inputs_hash}",
        "case_id": doc.get("case_id"),
        "as_of": doc["as_of"],
        "valuation_date": doc["valuation_date"],
        "config_version": doc.get("config_version"),
        "base_currency": doc.get("base_currency"),
        "units": doc.get("units"),
        "inputs_hash": inputs_hash,
        "model": {"id": model.get("id"), "version": model.get("version"),
                  "effective_date": model.get("effective_date")},
        "factors": factors,
        "portfolio": {"id": port.get("id"), "sensitivities": p_sens, "gross_sensitivity": gross_p},
        "portfolio_scenario_pnl": portfolio_scenario_pnl,
        "scenarios": scen_defs,
        "comparison": comparison,
        "reconciliation": recon,
        "assumptions_register": register,
        "limitations": limitations,
        "model_checks": {
            "all_tieouts_ok": all(all(c["tieouts"].values()) for c in comparison),
            "reconciliation_ok": all_recon_ok,
        },
        "disclaimer": DISCLAIMER,
    }


def _selftest() -> int:
    p = Path(__file__).resolve().parents[1] / "evals" / "files" / "hedge_input_example.json"
    doc = json.loads(p.read_text(encoding="utf-8"))
    pack = compute(doc)
    errors = []
    # 1. internal tie-outs across every candidate hedge
    for c in pack["comparison"]:
        for check, ok in c["tieouts"].items():
            if not ok:
                errors.append(f"hedge {c['hedge_id']} {check} failed")
    # 2. reconciliation to approved-engine totals must hold on the golden fixture
    if not pack["reconciliation"]["all_ok"]:
        errors.append("reconciliation to approved-engine totals failed")
    # 3. every assumption carries provenance + citation
    for a in pack["assumptions_register"]:
        if not str(a.get("provenance", "")).strip() or not str(a.get("citation", "")).strip():
            errors.append(f"assumption {a.get('id')} missing provenance/citation")
    # 4. reproducibility markers present
    for k in ("packet_id", "inputs_hash"):
        if not str(pack.get(k, "")).strip():
            errors.append(f"missing {k}")
    # deterministic diagnostics (also assertable by the eval harness)
    print(f"calculate selftest: portfolio gross_sensitivity={pack['portfolio']['gross_sensitivity']}")
    for c in pack["comparison"]:
        print(f"calculate selftest: hedge {c['hedge_id']} residual_gross={c['residual_gross']} "
              f"coverage_overall={c['coverage_overall']}")
    for sid, v in pack["portfolio_scenario_pnl"].items():
        print(f"calculate selftest: portfolio scenario {sid} pnl={v}")
    print(f"calculate selftest: reconciliation_ok={pack['model_checks']['reconciliation_ok']}")
    for e in errors:
        print("ERROR", e)
    print(f"calculate selftest: {len(errors)} error(s)")
    return 1 if errors else 0


def main(argv):
    if "--selftest" in argv:
        return _selftest()
    if argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
