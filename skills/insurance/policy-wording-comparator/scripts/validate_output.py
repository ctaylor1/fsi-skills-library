#!/usr/bin/env python3
"""Deterministic output validation for policy-wording-comparator.

Validates the final comparison pack (the calculate_or_transform core + a narrative) before it is
presented or delivered. This is the R3 prohibited-decision screen: it must fail closed on any
coverage/compliance/filing/closure language, on unevidenced material findings, on a track that does
not match the deterministic mapping, or on a missing legal/compliance handoff or disclaimer.

Checks:
  1. Every material finding has >= 1 cited evidence row (non-empty citation).
  2. Every escalate finding is also material (internal consistency).
  3. suggested_review_track equals the deterministic mapping from the findings.
  4. No coverage/compliance/filing/closure decision language (narrative + questions + notes).
  5. A non-empty legal_review_handoff is present when the track is escalated.
  6. The standing disclaimer is present.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DISCLAIMER = ("Comparison evidence only; not a coverage, compliance, or filing determination. "
              "A licensed professional must adjudicate; no form has been filed, approved, or bound.")

# Positive decision / filing / coverage / closure assertions an R3 skill must NOT make.
# Patterns are specific action/conclusion phrasings; neutral descriptions ("baseline filed form",
# "an added exclusion", "confirm filing implications") do not match.
PROHIBITED_PATTERNS = [
    r"\bapproved for filing\b", r"\bcleared for filing\b", r"\bclear(ed)? to file\b",
    r"\bready to file\b", r"\bfile the form\b", r"\bwe (will|should|can) file\b",
    r"\bapprove the (form|endorsement|wording)\b", r"\bthe form is approved\b",
    r"\bform is compliant\b", r"\bis compliant with\b", r"\bfully compliant\b",
    r"\bcertif(y|ies|ied) compliance\b", r"\bwe certify\b",
    r"\bcoverage (applies|is granted|is denied|does not apply|is afforded)\b",
    r"\bgrant coverage\b", r"\bdeny (the )?claim\b", r"\bdenies the claim\b",
    r"\bthe exclusion (does not|doesn'?t) apply\b", r"\bexclusion applies\b",
    r"\bbind coverage\b", r"\bcleared to bind\b", r"\bwe determine\b",
    r"\bclose (the )?review\b", r"\bno further review\b", r"\breview is complete\b",
    r"\bno action (is )?(needed|required)\b",
]


def _expected_track(findings: list) -> str:
    if any(f.get("escalate") for f in findings):
        return "Legal/compliance review required"
    if any(f.get("material") for f in findings):
        return "Standard review"
    return "No material changes"


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    findings = pack.get("findings") or []

    for f in findings:
        fid = f.get("finding_id", f.get("clause_id", "?"))
        if f.get("escalate") and not f.get("material"):
            errors.append(f"finding {fid} is escalate but not material (inconsistent)")
        if f.get("material"):
            ev = f.get("evidence") or []
            if not ev:
                errors.append(f"material finding {fid} has no cited evidence")
            for row in ev:
                if not (row.get("citation") or "").strip():
                    errors.append(f"material finding {fid} evidence row missing citation")

    exp = _expected_track(findings)
    if pack.get("suggested_review_track") != exp:
        errors.append(
            f"suggested_review_track {pack.get('suggested_review_track')!r} != deterministic {exp!r}")

    if exp == "Legal/compliance review required" and not (pack.get("legal_review_handoff") or "").strip():
        errors.append("track is 'Legal/compliance review required' but legal_review_handoff is empty")

    # scan free text (narrative + notes + questions + finding questions), NOT the disclaimer field
    text_parts = [str(pack.get("narrative", "")), str(pack.get("notes", ""))]
    text_parts += [str(q) for q in (pack.get("review_questions") or [])]
    text_parts += [str(f.get("review_question", "")) for f in findings]
    text = " ".join(text_parts)
    for pat in PROHIBITED_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"prohibited decision/filing language detected: {m.group(0)!r} "
                          "(R3 evidences and asks; it does not decide, file, or close)")

    haystack = (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower()
    if DISCLAIMER.lower() not in haystack:
        errors.append("missing standing disclaimer text")

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
