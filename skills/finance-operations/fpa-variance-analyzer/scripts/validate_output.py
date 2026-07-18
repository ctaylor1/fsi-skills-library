#!/usr/bin/env python3
"""Deterministic output validation for fpa-variance-analyzer.

Validates the final variance-analysis pack (the calculate_or_transform core + a narrative)
before it is presented or delivered. Checks:
  1. Every material finding has >= 1 cited evidence row.
  2. Driver attribution ties out: a finding claiming attribution_status "ok" must have
     drivers that sum (within tolerance) to its vs_budget variance.
  3. Run-rate impacts are labeled as estimates.
  4. suggested_priority equals the deterministic mapping from the material findings.
  5. No management-decision / forecast-commitment / restatement / advice language
     (narrative + notes + per-finding commentary).
  6. The standing disclaimer is present.
  7. caveats (alternative-explanation prompts) are included when any finding is material.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DEFAULT_RUN_RATE_ESCALATION = 250000.0
DEFAULT_ATTR_TOLERANCE = 1.0
DISCLAIMER = ("Variance analysis and draft commentary only; not a management decision, "
              "forecast commitment, or restatement of the financial records. Human review "
              "is required before external delivery.")

# Decision / commitment / restatement / advice assertions an R2 analyzer must NOT make.
# (An R2 skill analyzes and drafts; management decides, Finance commits guidance, Close
# restates/posts.)
PROHIBITED_PATTERNS = [
    r"\bwe (should|will|must|need to) (cut|reduce|eliminate|lay ?off|defund|approve|reject|hire|fire|freeze)\b",
    r"\bcut headcount\b", r"\bfreeze (hiring|the budget|headcount)\b",
    r"\brestat(e|ing|ement)\b",
    r"\b(post|book|record) (the|a|an) (journal|adjustment|entry|accrual)\b",
    r"\bapprove the (budget|forecast|reforecast|plan)\b",
    r"\breforecast to\b", r"\bnew official forecast\b", r"\bofficial guidance\b",
    r"\bguidance (is|to|of)\b", r"\bwe will (hit|deliver|achieve|exceed|miss|beat)\b",
    r"\bcommit to (the|a) (number|target|forecast|guidance)\b",
    r"\byou should (buy|sell|invest|divest)\b", r"\binvestment (advice|recommendation)\b",
    r"\b(buy|sell) (the )?(stock|shares|security|securities)\b",
]


def _expected_priority(pack: dict) -> str:
    esc_thr = float(pack.get("run_rate_escalation", DEFAULT_RUN_RATE_ESCALATION))
    mats = [f for f in (pack.get("findings") or []) if f.get("material")]
    escalator = any(
        f.get("attribution_status") in ("fail", "unattributed")
        or (f.get("persistence") == "recurring"
            and abs(f.get("run_rate_impact") or 0.0) >= esc_thr)
        for f in mats)
    if len(mats) >= 3 or escalator:
        return "Elevated"
    return "Standard" if mats else "Routine"


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    findings = pack.get("findings") or []
    mats = [f for f in findings if f.get("material")]
    tol = float(pack.get("attribution_tolerance", DEFAULT_ATTR_TOLERANCE))

    for f in mats:
        fid = f.get("line_id", "?")
        ev = f.get("evidence") or []
        if not ev:
            errors.append(f"material finding {fid} has no evidence")
        for row in ev:
            if not (row.get("citation") or "").strip():
                errors.append(f"material finding {fid} evidence row missing citation")

        # driver tie-out: an 'ok' claim must be independently reproducible
        status = f.get("attribution_status")
        var = (f.get("variance") or {}).get("vs_budget")
        if status == "ok":
            drivers = f.get("drivers") or []
            if not drivers:
                errors.append(f"material finding {fid} claims attribution 'ok' but has no drivers")
            elif var is not None:
                s = sum(float(d.get("amount") or 0.0) for d in drivers)
                if abs(float(var) - s) > tol:
                    errors.append(f"material finding {fid} attribution 'ok' but drivers {s} do not tie out to vs_budget {var}")

        # run-rate impacts must be labeled estimates
        if abs(f.get("run_rate_impact") or 0.0) > 0 and not f.get("run_rate_is_estimate"):
            errors.append(f"material finding {fid} has a run-rate impact not labeled as an estimate")

    exp = _expected_priority(pack)
    if pack.get("suggested_priority") != exp:
        errors.append(f"suggested_priority {pack.get('suggested_priority')!r} != deterministic {exp!r} "
                      f"for {len(mats)} material finding(s)")

    # scan free text (narrative + notes + commentary), NOT the disclaimer/caveats fields
    text = " ".join([str(pack.get("narrative", "")), str(pack.get("notes", ""))]
                    + [str(f.get("commentary", "")) for f in findings])
    for pat in PROHIBITED_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"prohibited decision/directive language detected: {m.group(0)!r} "
                          f"(R2 analyzes and drafts; it does not decide, commit, or restate)")

    if DISCLAIMER.lower() not in (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower():
        errors.append("missing standing disclaimer text")

    if mats and not pack.get("caveats"):
        errors.append("material findings present but no caveats (alternative-explanation prompts) included")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "pack_example.json"
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
