#!/usr/bin/env python3
"""Deterministic portfolio stress-test engine for portfolio-stress-test-runner.

Reads a stress-run input file (see validate_input.py), applies each *human-approved* scenario
(a set of shocks to risk factors) to an approved portfolio through an approved factor-
sensitivity model, and computes the scenario profit-and-loss (P&L) with a full driver
attribution by position and by factor. Every scenario carries its own tie-outs; the position
and factor attributions each reconcile to the scenario total; the stressed value reconciles
to base + P&L; and, where the firm supplies its official engine's totals, the run reconciles
to them. The run is reproducible from a hash of its inputs.

Position-factor P&L uses a first-order (delta) revaluation with an optional second-order
(convexity/gamma) term, applied consistently in both attributions so the walk always ties:

    contribution(i, f) = sensitivity(i, f) * shock(f) + 0.5 * convexity(i, f) * shock(f)**2

IMPORTANT: This produces an *illustrative stress-test run* only. It never invents a scenario
(scenarios are consumed from an approved source such as stress-test-scenario-designer) and
never issues investment advice, a recommendation, a hedge/rebalance instruction, or a
risk-limit or capital determination. Shocks and sensitivities are approved, documented
inputs, not the skill's judgment. See references/domain-rules.md.

Usage:
  python calculate_or_transform.py stress_input.json | --selftest
Prints the run pack JSON to stdout.
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

ROUND = 4            # currency precision
PCT_ROUND = 6        # percentage precision
DISCLAIMER = ("Illustrative stress-test run for analytical purposes only; not investment "
              "advice, not a recommendation to buy, sell, hold, hedge, rebalance, or de-risk "
              "any position or portfolio, and not a risk-limit or capital determination. "
              "Results execute human-approved scenarios against the stated portfolio and "
              "risk model and depend entirely on those approved scenario definitions, "
              "position data, and factor sensitivities, which a qualified human must review.")


def _num(node, default=0.0):
    if isinstance(node, dict):
        v = node.get("value", node.get("sensitivity"))
        return float(v) if v is not None else default
    return float(node) if node is not None else default


def _sens(node):
    return float(node.get("sensitivity")) if isinstance(node, dict) else float(node)


def _convex(node):
    if isinstance(node, dict) and node.get("convexity") is not None:
        return float(node["convexity"])
    return 0.0


def _prov(node):
    return (node.get("provenance", "") if isinstance(node, dict) else "")


def _cite(node):
    return (node.get("citation", "") if isinstance(node, dict) else "")


def compute(doc: dict) -> dict:
    base_value = float(doc["portfolio_base_value"])
    tol = _num(doc.get("reconciliation_tolerance"), 0.01) or 0.01
    factors = doc.get("risk_factors") or {}
    positions = doc["positions"]
    aet = doc.get("approved_engine_totals") or {}

    def run_scenario(s: dict) -> dict:
        shocks = {fid: float(v) for fid, v in (s.get("shocks") or {}).items()}
        pos_rows = []
        factor_pnl: dict[str, float] = {}
        scenario_pnl = 0.0
        for p in positions:
            exps = p.get("factor_exposures") or {}
            contribs = {}
            p_pnl = 0.0
            for fid, node in exps.items():
                shock = shocks.get(fid, 0.0)
                c = _sens(node) * shock + 0.5 * _convex(node) * (shock ** 2)
                c = round(c, ROUND)
                contribs[fid] = c
                p_pnl = round(p_pnl + c, ROUND)
                factor_pnl[fid] = round(factor_pnl.get(fid, 0.0) + c, ROUND)
            scenario_pnl = round(scenario_pnl + p_pnl, ROUND)
            pos_rows.append({
                "position_id": p.get("position_id"),
                "label": p.get("label"),
                "market_value": round(_num(p.get("market_value")), ROUND),
                "pnl": p_pnl,
                "pnl_pct_of_base": round(p_pnl / base_value, PCT_ROUND) if base_value else None,
                "factor_contributions": contribs,
            })

        # deterministic ordering: positions by P&L ascending (largest loss first);
        # factors by absolute P&L descending then factor_id for stable ties.
        pos_rows.sort(key=lambda r: (r["pnl"], r["position_id"]))
        factor_rows = [{
            "factor_id": fid,
            "label": (factors.get(fid) or {}).get("label"),
            "pnl": factor_pnl[fid],
            "pnl_pct_of_base": round(factor_pnl[fid] / base_value, PCT_ROUND) if base_value else None,
        } for fid in factor_pnl]
        factor_rows.sort(key=lambda r: (-abs(r["pnl"]), r["factor_id"]))

        stressed_value = round(base_value + scenario_pnl, ROUND)
        pnl_pct = round(scenario_pnl / base_value, PCT_ROUND) if base_value else None

        # reconciliation to the firm's approved/official stress engine, when supplied
        recon = None
        recon_ok = True
        if s.get("scenario_id") in aet:
            approved_total = round(float(aet[s["scenario_id"]]), ROUND)
            diff = round(scenario_pnl - approved_total, ROUND)
            recon_ok = abs(diff) <= tol
            recon = {"approved_engine_total": approved_total, "computed_total": scenario_pnl,
                     "difference": diff, "within_tolerance": recon_ok}

        # tie-outs (each re-checked independently in validate_output)
        pos_sum = round(sum(r["pnl"] for r in pos_rows), ROUND)
        fac_sum = round(sum(r["pnl"] for r in factor_rows), ROUND)
        pos_factor_ok = all(
            abs(round(sum(r["factor_contributions"].values()), ROUND) - r["pnl"]) <= tol
            for r in pos_rows)
        return {
            "scenario_id": s.get("scenario_id"),
            "label": s.get("label"),
            "type": s.get("type"),
            "approved": s.get("approved") is True,
            "shocks": shocks,
            "scenario_pnl": scenario_pnl,
            "stressed_value": stressed_value,
            "pnl_pct": pnl_pct,
            "attribution_by_position": pos_rows,
            "attribution_by_factor": factor_rows,
            "reconciliation": recon,
            "tieouts": {
                "position_sum_ok": abs(pos_sum - scenario_pnl) <= tol,
                "factor_sum_ok": abs(fac_sum - scenario_pnl) <= tol,
                "position_factor_ok": pos_factor_ok,
                "stressed_value_ok": abs(stressed_value - (base_value + scenario_pnl)) <= tol,
                "reconciliation_ok": recon_ok,
            },
        }

    scenarios = [run_scenario(s) for s in doc["scenarios"]]

    # provenance for every scenario, position, and factor sensitivity used
    register = []
    scen_provenance = []
    for s in doc["scenarios"]:
        register.append({
            "id": f"scenario:{s.get('scenario_id')}", "scope": "scenario-definition",
            "approved": s.get("approved") is True,
            "provenance": (s.get("source") or ""), "citation": (s.get("citation") or ""),
        })
        scen_provenance.append({
            "scenario_id": s.get("scenario_id"), "type": s.get("type"),
            "approved": s.get("approved") is True,
            "scenario_set_id": s.get("scenario_set_id"),
            "scenario_set_version": s.get("scenario_set_version"),
            "source": s.get("source"), "approval_ref": s.get("approval_ref"),
            "citation": s.get("citation"),
        })
    for p in positions:
        register.append({
            "id": f"position:{p.get('position_id')}", "scope": "portfolio-position",
            "value": round(_num(p.get("market_value")), ROUND),
            "provenance": _prov(p), "citation": _cite(p),
        })
        for fid, node in (p.get("factor_exposures") or {}).items():
            register.append({
                "id": f"exposure:{p.get('position_id')}:{fid}", "scope": "factor-sensitivity",
                "value": _sens(node), "convexity": _convex(node),
                "provenance": _prov(node), "citation": _cite(node),
            })

    # reproducibility hash over the numeric assumptions + approved scenario definitions
    hash_src = json.dumps({
        "portfolio_base_value": base_value,
        "positions": [{
            "position_id": p.get("position_id"),
            "market_value": _num(p.get("market_value")),
            "exposures": {fid: [_sens(n), _convex(n)] for fid, n in (p.get("factor_exposures") or {}).items()},
        } for p in positions],
        "scenarios": [{
            "scenario_id": s.get("scenario_id"),
            "scenario_set_id": s.get("scenario_set_id"),
            "scenario_set_version": s.get("scenario_set_version"),
            "shocks": {fid: float(v) for fid, v in (s.get("shocks") or {}).items()},
        } for s in doc["scenarios"]],
        "approved_engine_totals": {k: float(v) for k, v in aet.items()},
        "model_version": doc.get("model_version"),
        "config_version": doc.get("config_version"),
    }, sort_keys=True)
    inputs_hash = hashlib.sha256(hash_src.encode("utf-8")).hexdigest()[:16]

    all_tieouts_ok = all(all(s["tieouts"].values()) for s in scenarios)
    all_approved = all(s["approved"] for s in scenarios)
    recon_ok = all(s["tieouts"]["reconciliation_ok"] for s in scenarios)

    return {
        "run_id": f"stressrun-{str(doc['portfolio_id']).replace('*', '')}-{doc['as_of']}-{inputs_hash}",
        "portfolio_id": doc["portfolio_id"],
        "as_of": doc["as_of"],
        "run_date": doc["run_date"],
        "base_currency": doc.get("base_currency"),
        "units": doc.get("units"),
        "config_version": doc.get("config_version"),
        "model_version": doc.get("model_version"),
        "inputs_hash": inputs_hash,
        "portfolio_base_value": round(base_value, ROUND),
        "scenario_set_provenance": scen_provenance,
        "scenarios": scenarios,
        "assumptions_register": register,
        "run_checks": {
            "all_tieouts_ok": all_tieouts_ok,
            "all_scenarios_approved": all_approved,
            "reconciliation_ok": recon_ok,
        },
        "disclaimer": DISCLAIMER,
    }


def _selftest_errors(pack: dict) -> list[str]:
    """Independent re-check of the engine's own tie-outs over its bundled fixture."""
    errs = []
    base = float(pack["portfolio_base_value"])
    for s in pack["scenarios"]:
        sid = s["scenario_id"]
        pos_sum = round(sum(r["pnl"] for r in s["attribution_by_position"]), ROUND)
        fac_sum = round(sum(r["pnl"] for r in s["attribution_by_factor"]), ROUND)
        if abs(pos_sum - s["scenario_pnl"]) > 0.01:
            errs.append(f"scenario {sid}: position attribution {pos_sum} != scenario_pnl {s['scenario_pnl']}")
        if abs(fac_sum - s["scenario_pnl"]) > 0.01:
            errs.append(f"scenario {sid}: factor attribution {fac_sum} != scenario_pnl {s['scenario_pnl']}")
        if abs(s["stressed_value"] - (base + s["scenario_pnl"])) > 0.01:
            errs.append(f"scenario {sid}: stressed_value tie-out fails")
        if not all(s["tieouts"].values()):
            errs.append(f"scenario {sid}: a tie-out flag is false {s['tieouts']}")
    return errs


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "stress_input_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    pack = compute(doc)
    print(json.dumps(pack, indent=2))
    if "--selftest" in argv:
        errs = _selftest_errors(pack)
        for e in errs:
            print("ERROR", e)
        print(f"compute self-test: {len(errs)} error(s)")
        return 1 if errs else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
