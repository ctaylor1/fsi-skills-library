#!/usr/bin/env python3
"""Deterministic goal-progress computation for financial-goal-progress-analyzer.

Reads a goals file (see validate_input.py), and for each stated financial goal projects
its value at the target date under **approved, versioned assumptions**, computes a funded
ratio, maps it to a documented status band, quantifies the shortfall/surplus, and derives
**illustrative planning levers** (arithmetic what-ifs). It attaches evidence + citations to
every goal finding and emits a machine-readable core the SKILL wraps in a plain-language
analysis.

IMPORTANT: This produces source-linked *findings and illustrative levers* only. It never
produces a recommendation, a suitability determination, a guarantee of results, personalized
investment/tax advice, or any trade/filing/system-of-record change. Status bands and levers
map deterministically from the approved assumptions and are documented in
references/domain-rules.md.

Usage:
  python calculate_or_transform.py goals.json | --selftest
Prints the analysis JSON to stdout.
"""
from __future__ import annotations
import json, sys
from datetime import datetime
from pathlib import Path

# Approved assumptions are a versioned contract; these are only fallback defaults used when a
# field is absent. The real values come from the approved capital-market/planning config and
# the output records the assumptions_version so the analysis is reproducible.
DEFAULT_ASSUMPTIONS = {
    "expected_return_annual": 0.05,
    "inflation_annual": 0.025,
    "on_track_min": 1.00,        # funded ratio >= this -> On track
    "at_risk_min": 0.85,         # at_risk_min <= funded ratio < on_track_min -> At risk
    "max_extension_months": 600, # cap on the horizon-extension lever search
}
DISCLAIMER = (
    "Decision-support analysis only under approved assumptions; not a recommendation, "
    "suitability determination, guarantee of results, or investment/tax advice. No decision, "
    "trade, filing, or system-of-record change has been made."
)
VALID_TERMS = ("nominal", "real")


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _parse_date(s: str) -> datetime:
    return datetime.strptime(str(s)[:10], "%Y-%m-%d")


def _months_between(start: datetime, end: datetime) -> int:
    """Whole months from start to end (day-of-month aware). Negative if end precedes start."""
    m = (end.year - start.year) * 12 + (end.month - start.month)
    if end.day < start.day:
        m -= 1
    return m


def _fv(pv: float, pmt: float, rm: float, n: int) -> float:
    """Future value of a present balance plus an ordinary (period-end) annuity."""
    if n <= 0:
        return pv
    if rm == 0:
        return pv + pmt * n
    growth = (1.0 + rm) ** n
    return pv * growth + pmt * ((growth - 1.0) / rm)


def _required_pmt(pv: float, target_nominal: float, rm: float, n: int):
    """Level monthly contribution needed for pv to reach target_nominal in n months."""
    if n <= 0:
        return None
    if rm == 0:
        return (target_nominal - pv) / n
    growth = (1.0 + rm) ** n
    return (target_nominal - pv * growth) * rm / (growth - 1.0)


def _months_to_target(pv: float, pmt: float, rm: float, target_nominal: float, cap: int):
    """Smallest whole month count for pv+pmt to reach target_nominal (deterministic search).

    Returns None if the target is not reached within `cap` months (e.g., non-growing plan).
    """
    if _fv(pv, pmt, rm, 0) >= target_nominal:
        return 0
    for n in range(1, cap + 1):
        if _fv(pv, pmt, rm, n) >= target_nominal:
            return n
    return None


def _cite(goal: dict) -> str:
    return f"goals:{goal.get('source_ref', '?')}"


def _band(funded_ratio, on_track_min, at_risk_min) -> str:
    if funded_ratio >= on_track_min:
        return "On track"
    if funded_ratio >= at_risk_min:
        return "At risk"
    return "Off track"


def compute(doc: dict) -> dict:
    asmp = {**DEFAULT_ASSUMPTIONS, **(doc.get("assumptions") or {})}
    r = float(asmp["expected_return_annual"])
    infl = float(asmp["inflation_annual"])
    rm = r / 12.0
    on_track_min = float(asmp["on_track_min"])
    at_risk_min = float(asmp["at_risk_min"])
    cap = int(asmp["max_extension_months"])
    as_of = _parse_date(doc["as_of"])

    findings, not_evaluable = [], []

    for g in doc["goals"]:
        gid = g.get("goal_id")
        name = g.get("name", gid)
        target = _num(g.get("target_amount"))
        pv = _num(g.get("current_balance")) or 0.0
        pmt = _num(g.get("monthly_contribution")) or 0.0
        terms = g.get("target_terms", "nominal")
        cite = _cite(g)

        if target is None or target <= 0:
            not_evaluable.append({"goal_id": gid, "name": name,
                                  "why": "missing or non-positive target_amount", "citation": cite})
            continue
        try:
            tdate = _parse_date(g["target_date"])
        except (KeyError, ValueError):
            not_evaluable.append({"goal_id": gid, "name": name,
                                  "why": "missing or unparseable target_date", "citation": cite})
            continue

        n = _months_between(as_of, tdate)
        if n <= 0:
            not_evaluable.append({"goal_id": gid, "name": name,
                                  "why": f"target_date {g['target_date']} is not in the future "
                                         f"(n={n} months); progress is not projectable forward",
                                  "citation": cite})
            continue

        infl_factor = (1.0 + infl) ** (n / 12.0)
        projected_nominal = _fv(pv, pmt, rm, n)
        projected_real = projected_nominal / infl_factor

        # Compare projection to target in the goal's stated terms.
        if terms == "real":
            comparison = projected_real
            target_nominal = target * infl_factor
        else:
            comparison = projected_nominal
            target_nominal = target

        funded_ratio = round(comparison / target, 4)
        band = _band(funded_ratio, on_track_min, at_risk_min)
        gap = round(target - comparison, 2)  # >0 shortfall, <0 surplus (goal terms)

        # Illustrative planning levers (arithmetic what-ifs, NOT recommendations).
        levers = {}
        if band != "On track":
            req = _required_pmt(pv, target_nominal, rm, n)
            add_pmt = round(max(0.0, (req or 0.0) - pmt), 2)
            months = _months_to_target(pv, pmt, rm, target_nominal, cap)
            add_months = None if months is None else max(0, months - n)
            levers = {
                "additional_monthly_contribution": add_pmt,
                "additional_months_at_current_contribution": add_months,
                "target_reduction_to_match_projection": round(max(0.0, gap), 2),
                "note": ("Illustrative arithmetic only for advisor-client discussion; "
                         "not a recommendation or advice."),
            }

        findings.append({
            "goal_id": gid,
            "name": name,
            "target_amount": round(target, 2),
            "target_terms": terms,
            "target_date": g["target_date"],
            "months_to_target": n,
            "current_balance": round(pv, 2),
            "monthly_contribution": round(pmt, 2),
            "projected_value_nominal": round(projected_nominal, 2),
            "projected_value_real": round(projected_real, 2),
            "comparison_basis": round(comparison, 2),
            "funded_ratio": funded_ratio,
            "status": band,
            "shortfall_or_surplus": gap,
            "levers": levers,
            "evidence": [
                {"field": "goal_record", "citation": cite},
                {"field": "current_balance", "value": round(pv, 2),
                 "citation": f"portfolio:{g.get('balance_ref', g.get('source_ref', '?'))}"},
                {"field": "monthly_contribution", "value": round(pmt, 2),
                 "citation": f"cashflow:{g.get('contribution_ref', g.get('source_ref', '?'))}"},
                {"field": "assumptions", "value": doc.get("assumptions_version"),
                 "citation": f"assumptions:{doc.get('assumptions_version', '?')}"},
            ],
        })

    counts = {"On track": 0, "At risk": 0, "Off track": 0}
    for f in findings:
        counts[f["status"]] += 1

    return {
        "analysis_id": f"fgpa-{str(doc.get('client_id', 'client')).replace('*', '')}-{doc['as_of']}-0001",
        "client_id": doc.get("client_id"),
        "as_of": doc["as_of"],
        "assumptions_version": doc.get("assumptions_version"),
        "assumptions_used": {"expected_return_annual": r, "inflation_annual": infl,
                             "on_track_min": on_track_min, "at_risk_min": at_risk_min},
        "summary": {"goals_evaluated": len(findings), "not_evaluable": len(not_evaluable),
                    "status_counts": counts},
        "goals": findings,
        "not_evaluable": not_evaluable,
        "caveats": [
            "Projections are estimates under approved assumptions and will vary with markets, "
            "contributions, and time; they are not guarantees.",
            "Funded ratios and status bands are a triage aid for the advisor, not a suitability "
            "determination or a recommendation.",
        ],
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "goals_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
