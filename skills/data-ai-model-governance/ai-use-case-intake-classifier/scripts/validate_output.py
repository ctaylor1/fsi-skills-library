#!/usr/bin/env python3
"""Deterministic output validation for ai-use-case-intake-classifier.

Validates the final classification record (the calculate_or_transform core + a narrative) before it
is presented or routed. This is the R3 guardrail: the skill recommends a governance tier/path for
HUMAN adjudication; it must never render a binding governance decision. Checks:
  1. Every fired factor has >= 1 cited evidence row.
  2. governance_tier AND recommended_governance_path equal the deterministic mapping from
     fired_factors.
  3. human_adjudication_required is exactly true.
  4. No binding-decision / approval / clearance / exemption / closure language (narrative + notes +
     factor reasons; NOT the disclaimer field).
  5. required_reviews is non-empty.
  6. The standing disclaimer is present.

Usage:
  python validate_output.py record.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

HIGH_TRIGGERS = {"regulated_decision", "autonomous_action", "special_category_data", "high_materiality"}
DISCLAIMER = ("Provisional classification prepared for human governance adjudication only; it does "
              "not grant, waive, exempt, or close any governance review, and is not a deployment "
              "authorization.")
PATH_BY_TIER = {
    "Prohibited": "Prohibited-practice escalation - route to Legal/Ethics; do not proceed pending human adjudication",
    "High": "Full governance review",
    "Limited": "Standard governance review",
    "Minimal": "Lightweight review (register and attest)",
}

# Positive binding-decision / approval / closure assertions that R3 must NOT make. Worded to match
# affirmative statements, not the negated disclaimer (which says the output does NOT do these).
DECISION_PATTERNS = [
    r"\bis approved\b", r"\bare approved\b",
    r"\bapproved (for|to) (deploy|deployment|production|launch|proceed)",
    r"\bcleared (for|to) (deploy|deployment|production|launch|proceed)",
    r"\bcleared to proceed\b",
    r"\bno (further )?governance review (is )?(required|needed)\b",
    r"\bexempt from (governance|the) (review|oversight)\b",
    r"\bexempt from oversight\b",
    r"\bsign-?off (is )?granted\b", r"\bgovernance sign-?off\b",
    r"\bcase (is )?closed\b", r"\bintake (is )?closed\b",
    r"\bgreen-?lit\b", r"\bgreen-?light this\b",
    r"\bwe approve\b", r"\bwaive (the|this) (governance )?review\b",
    r"\bfit for production\b", r"\bfit for deployment\b",
]


def _expected_tier(fired: list[str]) -> str:
    f = set(fired)
    if "prohibited_practice_flag" in f:
        return "Prohibited"
    if (HIGH_TRIGGERS & f) or len(f) >= 3:
        return "High"
    return "Limited" if f else "Minimal"


def validate(rec: dict) -> list[str]:
    errors: list[str] = []
    factors = rec.get("factors") or []
    fired = [s["factor"] for s in factors if s.get("fired")]

    for s in factors:
        if s.get("fired"):
            ev = s.get("evidence") or []
            if not ev:
                errors.append(f"fired factor {s['factor']} has no evidence")
            for row in ev:
                if not (row.get("citation") or "").strip():
                    errors.append(f"fired factor {s['factor']} evidence row missing citation")

    exp_tier = _expected_tier(fired)
    if rec.get("governance_tier") != exp_tier:
        errors.append(f"governance_tier {rec.get('governance_tier')!r} != deterministic {exp_tier!r} for fired={fired}")
    exp_path = PATH_BY_TIER[exp_tier]
    if rec.get("recommended_governance_path") != exp_path:
        errors.append(f"recommended_governance_path != deterministic path for tier {exp_tier!r}")

    if rec.get("human_adjudication_required") is not True:
        errors.append("human_adjudication_required must be true (R3 requires human adjudication)")

    if not (rec.get("required_reviews")):
        errors.append("required_reviews is empty (every classification routes to at least one review)")

    # scan free text (narrative + notes + factor reasons), but NOT the disclaimer field
    text = " ".join([str(rec.get("narrative", "")), str(rec.get("notes", ""))]
                    + [str(s.get("reason", "")) for s in factors])
    for pat in DECISION_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"binding-decision/approval language detected: {m.group(0)!r} "
                          "(R3 recommends; a human adjudicates governance)")

    if DISCLAIMER.lower() not in (str(rec.get("narrative", "")) + " " + str(rec.get("disclaimer", ""))).lower():
        errors.append("missing standing disclaimer text")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "classification_example.json"
        rec = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        rec = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        rec = json.loads(sys.stdin.read())
    errors = validate(rec)
    for e in errors:
        print("ERROR", e)
    print(f"output validation: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
