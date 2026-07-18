#!/usr/bin/env python3
"""Deterministic output validation for best-execution-reviewer.

Validates the final review pack (the calculate_or_transform core + a narrative) before it
is presented or delivered. Enforces the R3 guardrail: findings + cited evidence only, with
NO regulated decision, closure, disposition, attestation, or filing language. Checks:
  1. Every fired finding has >= 1 cited evidence row.
  2. Every fired finding type is a recognized best-execution check.
  3. suggested_disposition equals the deterministic mapping from fired_findings.
  4. No determination / closure / filing / attestation language (narrative + notes + reasons).
  5. The standing disclaimer is present.
  6. fp_checks (false-positive prompts) are included when any finding fired.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise (fail closed).
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ESCALATORS = {"price_materially_off", "venue_off_policy", "exception_undocumented"}
KNOWN_FINDINGS = {
    "price_outside_benchmark", "price_materially_off", "slow_execution",
    "low_fill_rate", "high_cost", "venue_off_policy", "exception_undocumented",
}
DISCLAIMER_KEY = "not a best-execution or compliance determination"
# Regulated decision / closure / filing / attestation language an R3 review must NOT contain.
PROHIBITED_PATTERNS = [
    r"\b(is|was|are|were) (fully )?compliant\b",
    r"\bcompliant with best[- ]execution\b",
    r"\bbest[- ]execution (was |is |has been )?(achieved|satisfied|met|obtained)\b",
    r"\bno (best[- ]execution )?breach\b",
    r"\b(is|was|are|were) in breach\b",
    r"\bbreach (is |was )?(confirmed|established)\b",
    r"\b(we|i) (hereby )?determine\b",
    r"\b(final|our) determination\b",
    r"\b(conclude|concluded) that best[- ]execution\b",
    r"\bcase closed\b",
    r"\bclose (the |this )?(case|exception|review|finding)\b",
    r"\bdisposition(ed)? as (compliant|passed|closed|no[- ]issue)\b",
    r"\bno further action (is )?(required|needed|necessary)\b",
    r"\bcleared of\b",
    r"\bsign(ed)? off\b",
    r"\battest(ation)?\b",
    r"\bfile (a |the |this )?(report|filing|form|rts) (with|to)\b",
    r"\bself[- ]report(ed|ing)? to (the )?(regulator|finra|sec|fca)\b",
    r"\bwrite (this )?to the system of record\b",
]


def _expected_disposition(fired) -> str:
    if any(x in ESCALATORS for x in fired) or len(fired) >= 3:
        return "Escalate"
    return "Review" if fired else "Pass"


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    findings = pack.get("findings") or []
    fired = [f["finding"] for f in findings if f.get("fired")]

    for f in findings:
        if f.get("fired"):
            if f["finding"] not in KNOWN_FINDINGS:
                errors.append(f"unrecognized fired finding type {f['finding']!r}")
            ev = f.get("evidence") or []
            if not ev:
                errors.append(f"fired finding {f['finding']} has no evidence")
            for row in ev:
                if not (row.get("citation") or "").strip():
                    errors.append(f"fired finding {f['finding']} evidence row missing citation")

    exp = _expected_disposition(fired)
    if pack.get("suggested_disposition") != exp:
        errors.append(f"suggested_disposition {pack.get('suggested_disposition')!r} != deterministic {exp!r} for fired={fired}")

    # scan free text (narrative + notes + finding reasons), but NOT the disclaimer field
    text = " ".join([str(pack.get("narrative", "")), str(pack.get("notes", ""))]
                    + [str(f.get("reason", "")) for f in findings])
    for pat in PROHIBITED_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"regulated decision/closure/filing language detected: {m.group(0)!r} "
                          "(R3 evidences and recommends; it does not decide, close, or file)")

    disc = (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower()
    if DISCLAIMER_KEY not in disc:
        errors.append("missing standing disclaimer text")

    if fired and not pack.get("fp_checks"):
        errors.append("findings fired but no fp_checks (false-positive prompts) included")

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
