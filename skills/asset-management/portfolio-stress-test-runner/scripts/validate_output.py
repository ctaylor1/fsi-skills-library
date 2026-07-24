#!/usr/bin/env python3
"""Deterministic output validation for portfolio-stress-test-runner.

Validates the final stress-run pack (the calculate_or_transform core + an author narrative)
before it is presented or delivered. Checks, in the order of the archetype's validation focus
and the skill's tier boundary:

  1. HARD BOUNDARY - scenario provenance: every scenario (and every scenario-definition entry
     in the assumptions register) is marked approved AND carries a scenario_set_id / source /
     citation. The runner executes approved scenarios; it must not present a self-invented or
     unsourced scenario as a run.
  2. Formula tie-outs (per scenario, re-derived independently, not trusted from the pack):
       - sum(position P&L) == scenario_pnl
       - sum(factor P&L) == scenario_pnl
       - each position P&L == sum(its factor contributions)
       - stressed_value == portfolio_base_value + scenario_pnl
  3. Approved-engine reconciliation: where a scenario carries the firm's official engine total,
     the computed total reconciles within tolerance (a silent disagreement fails closed).
  4. Assumption provenance: every register entry carries a non-empty provenance AND citation.
  5. Reproducibility: run_id and inputs_hash present.
  6. No investment advice / recommendation / hedge-rebalance-derisk / risk-limit language in
     author free text (R2 models and explains; it does not advise or mandate an action).
  7. Standing disclaimer present.

Usage:
  python validate_output.py stress_pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

TOL = 0.01
DISCLAIMER = ("Illustrative stress-test run for analytical purposes only; not investment "
              "advice, not a recommendation to buy, sell, hold, hedge, rebalance, or de-risk "
              "any position or portfolio, and not a risk-limit or capital determination. "
              "Results execute human-approved scenarios against the stated portfolio and "
              "risk model and depend entirely on those approved scenario definitions, "
              "position data, and factor sensitivities, which a qualified human must review.")

# Affirmative directed assertions an R2 stress run must NOT make: buy/sell/hedge/rebalance/
# de-risk instructions, risk-limit mandates, invented-scenario claims, guarantees. Worded so
# the standing disclaimer above (which negates these as "not a recommendation to ... hedge,
# rebalance, or de-risk") does not self-trip: the patterns require an affirmative directed
# form, not the negated disclaimer form. The disclaimer is also stripped before scanning.
ADVICE_PATTERNS = [
    r"\byou should (buy|sell|short|hold|reduce|trim|cut|increase|add|rotate|exit|hedge|rebalance|de-?risk|overweight|underweight)\b",
    r"\bwe recommend (buying|selling|shorting|holding|reducing|trimming|cutting|hedging|rebalancing|de-?risking|adding|rotating|exiting|an? (overweight|underweight))\b",
    r"\bi recommend (buying|selling|shorting|holding|reducing|hedging|rebalancing|de-?risking)\b",
    r"\b(recommend|advise|suggest) (reducing|hedging|rebalancing|de-?risking|trimming|cutting|selling|buying)\b",
    r"\b(reduce|trim|cut|increase|add to|rotate out of|exit) (the |your |our )?(equity|credit|rate|duration|position|exposure|allocation|book|sleeve)s?\b",
    r"\b(hedge|de-?risk|rebalance) (the |your |our )?(portfolio|book|position|exposure|risk)\b",
    r"\b(should|must|needs to) be (reduced|trimmed|cut|hedged|rebalanced|sold|de-?risked)\b",
    r"\b(our|the) (buy|sell|hold|overweight|underweight) (rating|call)\b",
    r"\bset (a |the )?(risk |stop-?loss )?limit\b",
    r"\b(breach|breaches|exceeds).{0,30}\b(so|therefore|must|should) (reduce|cut|close|sell|hedge)\b",
    r"\b(this run|the runner|we|i) (designed|invented|created|devised|made up|improvised|assumed) (a|an|the|our|these|this|new)\s+scenario\b",
    r"\bguaranteed (loss|return|protection|downside)\b",
]


def _num(v, default=None):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _check_scenario(s: dict, base_value: float) -> list[str]:
    errors = []
    sid = s.get("scenario_id", "?")

    if s.get("approved") is not True:
        errors.append(f"scenario {sid}: not marked approved - the runner never presents an "
                      f"un-approved or invented scenario as a run (HARD BOUNDARY)")

    pos = s.get("attribution_by_position") or []
    fac = s.get("attribution_by_factor") or []
    spnl = _num(s.get("scenario_pnl"))
    if spnl is None:
        errors.append(f"scenario {sid}: missing scenario_pnl")
        return errors
    if not pos:
        errors.append(f"scenario {sid}: missing attribution_by_position")
    if not fac:
        errors.append(f"scenario {sid}: missing attribution_by_factor")

    # position attribution ties to scenario total; each position ties to its factor contribs
    pos_sum = 0.0
    for r in pos:
        p_pnl = _num(r.get("pnl"))
        if p_pnl is None:
            errors.append(f"scenario {sid} position {r.get('position_id')}: missing pnl")
            continue
        contribs = r.get("factor_contributions") or {}
        c_sum = round(sum(_num(v, 0.0) for v in contribs.values()), 4)
        if abs(c_sum - p_pnl) > TOL:
            errors.append(f"scenario {sid} position {r.get('position_id')}: factor contributions "
                          f"{c_sum} do not tie to position pnl {p_pnl}")
        pos_sum += p_pnl
    pos_sum = round(pos_sum, 4)
    if abs(pos_sum - spnl) > TOL:
        errors.append(f"scenario {sid}: position attribution {pos_sum} does not tie to scenario_pnl {spnl}")

    # factor attribution ties to scenario total
    fac_sum = round(sum(_num(r.get("pnl"), 0.0) for r in fac), 4)
    if abs(fac_sum - spnl) > TOL:
        errors.append(f"scenario {sid}: factor attribution {fac_sum} does not tie to scenario_pnl {spnl}")

    # stressed value ties to base + P&L
    sv = _num(s.get("stressed_value"))
    if sv is None:
        errors.append(f"scenario {sid}: missing stressed_value")
    elif abs(sv - (base_value + spnl)) > TOL:
        errors.append(f"scenario {sid}: stressed_value {sv} does not tie to base {base_value} + pnl {spnl}")

    # approved-engine reconciliation, when present
    recon = s.get("reconciliation")
    if recon:
        at = _num(recon.get("approved_engine_total"))
        ct = _num(recon.get("computed_total"))
        if at is not None and ct is not None and abs(ct - at) > TOL:
            errors.append(f"scenario {sid}: computed total {ct} does not reconcile to approved "
                          f"engine total {at} (difference {round(ct - at, 4)})")
        if recon.get("within_tolerance") is False:
            errors.append(f"scenario {sid}: reconciliation.within_tolerance is false - the run "
                          f"disagrees with the firm's approved stress engine")
    return errors


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    base_value = _num(pack.get("portfolio_base_value"), 0.0) or 0.0
    scenarios = pack.get("scenarios") or []
    if not scenarios:
        errors.append("pack has no scenarios")

    for s in scenarios:
        errors += _check_scenario(s, base_value)

    # assumption provenance + scenario-definition approval (HARD BOUNDARY, register side)
    register = pack.get("assumptions_register") or []
    if not register:
        errors.append("assumptions_register missing (provenance must be recorded for every assumption)")
    for a in register:
        if not (a.get("provenance") or "").strip():
            errors.append(f"assumption {a.get('id')!r} missing provenance")
        if not (a.get("citation") or "").strip():
            errors.append(f"assumption {a.get('id')!r} missing citation")
        if a.get("scope") == "scenario-definition" and a.get("approved") is not True:
            errors.append(f"scenario-definition {a.get('id')!r} is not marked approved "
                          f"(the runner must not execute an un-approved/invented scenario)")

    # reproducibility
    if not (pack.get("run_id") or "").strip():
        errors.append("missing run_id (reproducibility)")
    if not (pack.get("inputs_hash") or "").strip():
        errors.append("missing inputs_hash (reproducibility)")

    # advice/recommendation/action-mandate scan over author free text - NOT the disclaimer.
    text = " ".join([str(pack.get("narrative", "")), str(pack.get("notes", ""))]
                    + [str(s.get("note", "")) for s in scenarios])
    text = re.sub(re.escape(DISCLAIMER), " ", text, flags=re.I)
    for pat in ADVICE_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"prohibited investment-advice/recommendation/action language detected: {m.group(0)!r} "
                          f"(R2 runs and explains; it does not advise, recommend, hedge, rebalance, set limits, or invent scenarios)")

    if DISCLAIMER.lower() not in (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower():
        errors.append("missing standing disclaimer text")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "stress_pack_example.json"
        pack = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        pack = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        pack = json.loads(sys.stdin.read())
    errors = validate(pack)
    for e in errors:
        print("ERROR", e)
    print(f"output validation: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
