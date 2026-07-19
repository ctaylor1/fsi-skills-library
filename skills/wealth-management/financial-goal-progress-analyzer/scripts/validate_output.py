#!/usr/bin/env python3
"""Deterministic output validation for financial-goal-progress-analyzer.

Validates the final goal-progress analysis (the calculate_or_transform core + a narrative)
before it is presented or delivered. Fails closed on any miss. Checks:
  1. Every evaluated goal has a status band and >= 1 cited evidence row.
  2. Each goal's status equals the deterministic band mapping from its funded_ratio.
  3. summary.status_counts ties to the per-goal statuses.
  4. Any goal not "On track" carries illustrative planning levers.
  5. No prohibited decision / recommendation / advice / guarantee / trade / filing language
     appears in the narrative or notes (R3 evidences and recommends levers; it never decides).
  6. The standing disclaimer is present.

Usage:
  python validate_output.py analysis.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

VALID_STATUS = {"On track", "At risk", "Off track"}
DISCLAIMER = (
    "Decision-support analysis only under approved assumptions; not a recommendation, "
    "suitability determination, guarantee of results, or investment/tax advice. No decision, "
    "trade, filing, or system-of-record change has been made."
)
DEFAULT_ON_TRACK_MIN = 1.00
DEFAULT_AT_RISK_MIN = 0.85

# Positive decision / recommendation / advice / action assertions an R3 analysis must NOT make.
# (Scanned only over free-text narrative + notes; controlled boilerplate is not scanned.)
DECISION_PATTERNS = [
    r"\bguarantee(d|s)?\b",
    r"\bwe recommend\b", r"\bi recommend\b",
    r"\brecommend(s|ed|ing)?\s+(that\s+)?(you|the client|buying|selling|allocating|investing|moving|switching)\b",
    r"\byou should\b", r"\bthe client should\b",
    r"\bis suitable\b", r"\bsuitab\w*\s+(for the client|is met|approved)\b",
    r"\bapprove(d|s)?\s+the\s+(recommendation|trade|order|allocation|plan)\b",
    r"\b(place|execute|submit|enter|initiate)\s+(the\s+|a\s+)?(trade|order|rebalance|transfer)\b",
    r"\b(buy|sell|purchase)\s+(the\s+|this\s+|these\s+|your\s+)?(fund|funds|security|securities|shares|etf|stock|position|holding)\b",
    r"\bfile\s+(a\s+|the\s+)\w+",
    r"\bclose\s+(the\s+)?(goal|case|plan|account)\b",
    r"\bpost\s+(a\s+|the\s+)?journal\b",
    r"\bwill\s+(reach|achieve|meet|be fully funded)\b",
    r"\bcommit(s|ted)?\s+the\s+client\b",
]


def _band(fr, on_track_min, at_risk_min):
    if fr >= on_track_min:
        return "On track"
    if fr >= at_risk_min:
        return "At risk"
    return "Off track"


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    goals = pack.get("goals") or []
    asmp = pack.get("assumptions_used") or {}
    on_track_min = float(asmp.get("on_track_min", DEFAULT_ON_TRACK_MIN))
    at_risk_min = float(asmp.get("at_risk_min", DEFAULT_AT_RISK_MIN))

    if not goals and not (pack.get("not_evaluable")):
        errors.append("analysis has neither evaluated goals nor not_evaluable entries")

    counts = {"On track": 0, "At risk": 0, "Off track": 0}
    for g in goals:
        gid = g.get("goal_id", "?")
        status = g.get("status")
        if status not in VALID_STATUS:
            errors.append(f"goal {gid}: invalid/missing status {status!r}")
            continue
        counts[status] += 1

        ev = g.get("evidence") or []
        cited = [e for e in ev if str(e.get("citation", "")).strip()]
        if not cited:
            errors.append(f"goal {gid}: no cited evidence row")

        fr = g.get("funded_ratio")
        if not isinstance(fr, (int, float)):
            errors.append(f"goal {gid}: missing numeric funded_ratio")
        else:
            exp = _band(fr, on_track_min, at_risk_min)
            if exp != status:
                errors.append(f"goal {gid}: status {status!r} != deterministic band {exp!r} "
                              f"for funded_ratio {fr}")

        if status != "On track":
            lv = g.get("levers") or {}
            if not lv or lv.get("additional_monthly_contribution") is None:
                errors.append(f"goal {gid}: status {status!r} but no illustrative levers provided")

    declared = (pack.get("summary") or {}).get("status_counts")
    if declared is not None and declared != counts:
        errors.append(f"summary.status_counts {declared} != recomputed {counts}")

    # scan free text only (narrative + notes); controlled boilerplate (caveats/disclaimer/
    # lever notes) is not scanned.
    text = " ".join([str(pack.get("narrative", "")), str(pack.get("notes", ""))])
    for pat in DECISION_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"prohibited decision/recommendation/advice language detected: "
                          f"{m.group(0)!r} (R3 evidences + proposes levers; it does not decide/advise)")

    disc_hay = (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower()
    if DISCLAIMER.lower() not in disc_hay:
        errors.append("missing standing disclaimer text")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "analysis_example.json"
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
