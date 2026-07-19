#!/usr/bin/env python3
"""Deterministic stress-scenario design engine for stress-test-scenario-designer.

Reads a scenario-design file (see validate_input.py), and for each scenario computes an
explainable severity score, projects each binding constraint through a transparent linear
transmission model, measures the distance to each constraint's breach point, and derives a
reverse-stress scaling multiple for the target constraint. It then maps the fully
deterministic set of structural, coverage, monotonicity, and plausibility flags to a
readiness band.

IMPORTANT: This produces *design evidence and recommendations only* — a candidate scenario
set for human challenge and adjudication. It never adopts a scenario, makes a capital or
liquidity decision, sets a limit, certifies a model, or produces a regulatory submission.
The readiness band is a completeness/quality gate for reviewers, not an approval. All
mappings are documented in references/domain-rules.md.

Usage:
  python calculate_or_transform.py design.json | --selftest
Prints the scenario-design JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

DISCLAIMER = ("Scenario design evidence and recommendations only; not an approved stress "
              "scenario, a capital or liquidity decision, a set limit, or a regulatory "
              "submission. Human adjudication (risk committee / model risk / board) is "
              "required before adoption.")
SEVERITY_ORDER = {"baseline": 0, "adverse": 1, "severely_adverse": 2}


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _baseline_values(scenarios: list) -> dict:
    """The baseline scenario's variable values define the zero-shock reference point."""
    for s in scenarios:
        if s.get("severity") == "baseline":
            return {v["factor"]: _num(v["value"]) for v in s.get("variables", [])
                    if _num(v.get("value")) is not None}
    return {}


def compute(doc: dict) -> dict:
    scenarios_in = doc.get("scenarios", [])
    factors = {f["factor"]: f for f in doc.get("risk_factors", [])}
    constraints = doc.get("binding_constraints", [])
    impact_model = doc.get("impact_model", {})
    base_vals = _baseline_values(scenarios_in)

    scenarios_out = []
    for s in scenarios_in:
        name = s.get("name")
        severity = s.get("severity")
        var_vals = {v["factor"]: _num(v["value"]) for v in s.get("variables", [])
                    if _num(v.get("value")) is not None}
        shock = {fac: round(val - base_vals.get(fac, val), 6) for fac, val in var_vals.items()}

        # explainable severity = impact-weighted L1 size of the shock across constraints
        severity_score = 0.0
        impacts = []
        for c in constraints:
            metric = c["metric"]
            betas = impact_model.get(metric, {})
            impact_sum = 0.0
            for fac, beta in betas.items():
                impact_sum += _num(beta) * shock.get(fac, 0.0)
            impact_sum = round(impact_sum, 4)
            starting = _num(c.get("starting_value"))
            limit = _num(c.get("limit"))
            direction = c.get("direction")
            stressed = round(starting + impact_sum, 4) if starting is not None else None
            if stressed is None or limit is None:
                distance, breached = None, None
            elif direction == "min":
                distance = round(stressed - limit, 4)   # positive = headroom above floor
                breached = stressed < limit
            else:  # "max" ceiling
                distance = round(limit - stressed, 4)   # positive = headroom below ceiling
                breached = stressed > limit
            impacts.append({"constraint": metric, "impact_sum": impact_sum,
                            "stressed_value": stressed, "limit": limit,
                            "direction": direction, "distance_to_breach": distance,
                            "breached": breached})
            severity_score += abs(impact_sum)
        severity_score = round(severity_score, 4)

        # coverage: every constraint's transmission betas must resolve to defined,
        # in-scenario factors; every stress factor should feed at least one constraint.
        coverage_gaps = []
        for c in constraints:
            for fac in impact_model.get(c["metric"], {}):
                if fac not in factors:
                    coverage_gaps.append(f"{c['metric']} beta references undefined factor '{fac}'")
                elif fac not in var_vals:
                    coverage_gaps.append(f"{c['metric']} beta factor '{fac}' absent from scenario '{name}'")
        modeled_factors = {fac for c in constraints for fac in impact_model.get(c["metric"], {})}
        for fac in var_vals:
            if fac not in modeled_factors:
                coverage_gaps.append(f"factor '{fac}' has no transmission channel to any constraint")

        # plausibility: severe-but-plausible band per factor (only stress scenarios floored)
        plausibility_flags = []
        for fac, sh in shock.items():
            fdef = factors.get(fac, {})
            pmax = _num(fdef.get("plausible_max_shock"))
            smin = _num(fdef.get("severe_min_shock"))
            if pmax is not None and abs(sh) > pmax:
                plausibility_flags.append(f"{fac} shock {sh} exceeds plausible band {pmax} (implausibly severe)")
            if severity == "severely_adverse" and smin is not None and abs(sh) < smin:
                plausibility_flags.append(f"{fac} severely-adverse shock {sh} below severe floor {smin} (insufficiently severe)")

        channels = s.get("transmission_channels") or []
        assumptions = s.get("assumptions") or []
        actions = s.get("management_actions") or []
        components_missing = []
        if not channels:
            components_missing.append("transmission_channels")
        if not assumptions:
            components_missing.append("assumptions")
        if severity != "baseline" and not actions:
            components_missing.append("management_actions")

        scenarios_out.append({
            "name": name, "severity": severity, "severity_score": severity_score,
            "shock_vector": shock, "impacts": impacts,
            "transmission_channels": channels, "assumptions": assumptions,
            "management_actions": actions,
            "coverage_gaps": coverage_gaps, "plausibility_flags": plausibility_flags,
            "components_missing": components_missing,
        })

    # severity monotonicity across the ordered ladder (baseline < adverse < severely_adverse)
    ladder = sorted([s for s in scenarios_out if s["severity"] in SEVERITY_ORDER],
                    key=lambda s: SEVERITY_ORDER[s["severity"]])
    monotonic = all(ladder[i]["severity_score"] < ladder[i + 1]["severity_score"]
                    for i in range(len(ladder) - 1)) if len(ladder) >= 2 else True

    # reverse stress: scale the target scenario's shock vector to reach the target constraint
    rs_in = doc.get("reverse_stress") or {}
    reverse_stress = None
    if rs_in:
        target_name = rs_in.get("scenario")
        target_metric = rs_in.get("constraint")
        sc = next((s for s in scenarios_out if s["name"] == target_name), None)
        cimp = next((i for i in (sc["impacts"] if sc else []) if i["constraint"] == target_metric), None)
        cdef = next((c for c in constraints if c["metric"] == target_metric), None)
        if cimp and cdef and cimp["impact_sum"] not in (None, 0):
            starting = _num(cdef.get("starting_value"))
            limit = _num(cdef.get("limit"))
            lam = (limit - starting) / cimp["impact_sum"]
            if lam <= 0:
                reverse_stress = {"scenario": target_name, "constraint": target_metric,
                                  "impact_sum": cimp["impact_sum"], "scaling_multiple": None,
                                  "interpretation": "constraint is not reachable by scaling this scenario in its stress direction"}
            else:
                lam = round(lam, 2)
                if lam < 1:
                    interp = (f"the {target_name} scenario already reaches the {target_metric} "
                              f"limit at {lam}x of its full severity")
                else:
                    interp = (f"the {target_name} shock vector would need to be amplified about "
                              f"{lam}x for {target_metric} to reach its {limit} limit")
                reverse_stress = {"scenario": target_name, "constraint": target_metric,
                                  "impact_sum": cimp["impact_sum"], "scaling_multiple": lam,
                                  "interpretation": interp}
        else:
            reverse_stress = {"scenario": target_name, "constraint": target_metric,
                              "impact_sum": cimp["impact_sum"] if cimp else None,
                              "scaling_multiple": None,
                              "interpretation": "insufficient impact data to derive a reverse-stress multiple"}

    # deterministic readiness band (documented in references/domain-rules.md)
    any_missing = any(s["components_missing"] for s in scenarios_out)
    any_coverage = any(s["coverage_gaps"] for s in scenarios_out)
    any_plausibility = any(s["plausibility_flags"] for s in scenarios_out)
    ready = not (any_missing or any_coverage or any_plausibility) and monotonic
    readiness_band = "Ready-for-review" if ready else "Not-ready"

    return {
        "design_id": doc.get("design_id") or f"sdp-{doc.get('as_of', 'na')}-0001",
        "as_of": doc.get("as_of"),
        "config_version": doc.get("config_version"),
        "horizon_quarters": doc.get("horizon_quarters"),
        "binding_constraints": constraints,
        "scenarios": scenarios_out,
        "severity_monotonic": monotonic,
        "reverse_stress": reverse_stress,
        "readiness_band": readiness_band,
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "scenario_design_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
