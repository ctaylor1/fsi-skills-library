#!/usr/bin/env python3
"""Deterministic output validation for policy-document-explainer.

Confirms the plain-language explanation is internally consistent, fully cited, and free of
coverage-determination / eligibility / claim-decision / advice language BEFORE it is
presented or delivered.

Checks:
  1. Explanation lists at least one element; each element has a non-empty plain_summary.
  2. Each element's element_type is a recognized policy-element type.
  3. Each element carries a non-empty citation.
  4. sections_explained_count ties to the number of elements listed.
  5. Narrative / element summaries / notes contain no coverage-determination, eligibility,
     claim-decision, or advice/recommendation phrasing (R1 is informational only).
  6. The standing informational-only disclaimer is present.

Neutral third-person description of what the document says (e.g. "Section I excludes flood")
is permitted; determinations about the reader's situation or a claim are not.

Output schema (JSON):
{
  "explanation_id","policy_id","form_edition","effective_date","expiration_date",
  "sections_explained_count": int,
  "elements":[{"section_id","element_type","plain_summary","citation"}],
  "data_gaps":[...],
  "narrative":"...",
  "disclaimer":"..."
}

Usage:
  python validate_output.py explanation.json
  python validate_output.py --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

KNOWN_TYPES = {
    "coverage", "exclusion", "condition", "definition", "endorsement",
    "declaration", "premium", "other",
}

# Determination / eligibility / claim-decision / advice phrasing. These describe the
# reader's situation or a claim, or tell the reader what to do — none of which an
# informational explainer may produce. Neutral description of the document is NOT matched.
PROHIBITED_PATTERNS = [
    # Coverage determination about the reader / a specific claim
    r"\byou(?:'re| are)?(?:n't| not)? covered\b",
    r"\byour (?:claim|loss|damage|incident|situation) (?:is|are|will be|would be|isn'?t|won'?t be)\b",
    r"\bthis (?:claim|loss|incident|damage|event) (?:is|would be|will be|isn'?t|won'?t be)\b",
    r"\b(?:claim|loss) (?:is|are|will be|would be) (?:approved|denied|payable|paid|covered)\b",
    r"\bwe (?:will|would|won'?t|will not) pay\b",
    r"\byou will be (?:paid|reimbursed|covered)\b",
    # Eligibility
    r"\byou (?:qualify|are eligible|do not qualify|are not eligible|don'?t qualify)\b",
    # Advice / recommendation
    r"\bwe (?:recommend|suggest|advise)\b",
    r"\bi (?:recommend|suggest|advise)\b",
    r"\byou should (?:buy|purchase|drop|cancel|switch|add|increase|decrease|reduce|get|keep|consider|remove|file)\b",
    r"\byou (?:ought to|might want to|need to buy)\b",
    r"\b(?:better|best) (?:policy|coverage|option|choice|plan)\b",
    r"\b(?:under|over)-?insured\b",
    r"\b(?:not enough|too little|too much) coverage\b",
    r"\b(?:legal|financial|tax) advice\b",
    r"\bthis (?:policy|coverage) is (?:right|wrong|suitable|unsuitable|appropriate) for you\b",
]
DISCLAIMER_RE = re.compile(
    r"informational.*only.*not .*(coverage determination|claim decision|advice)", re.I)
# The standing disclaimer legitimately contains the word "advice"; strip that one sentence
# before the language screen so the required disclaimer never false-trips the advice check.
DISCLAIMER_STRIP = re.compile(
    r"informational[^.]*?(?:coverage determination|claim decision|advice)[^.]*\.", re.I)


def validate(s: dict) -> list[str]:
    errors: list[str] = []
    elements = s.get("elements") or []
    if not elements:
        return ["explanation missing elements"]

    for e in elements:
        eid = e.get("section_id", "?")
        if not (e.get("plain_summary") or "").strip():
            errors.append(f"element {eid}: missing plain_summary")
        if not (e.get("citation") or "").strip():
            errors.append(f"element {eid}: missing citation")
        et = e.get("element_type")
        if et not in KNOWN_TYPES:
            errors.append(f"element {eid}: element_type {et!r} not a recognized policy-element type")

    count = s.get("sections_explained_count")
    if count is None:
        errors.append("missing sections_explained_count")
    elif count != len(elements):
        errors.append(f"sections_explained_count {count} != number of elements {len(elements)}")

    # Language screen over all human-readable text in the explanation.
    text = " ".join(str(s.get(k, "")) for k in ("narrative", "notes"))
    text += " " + " ".join(str(e.get("plain_summary", "")) for e in elements)
    text += " " + json.dumps(s.get("data_gaps", ""))
    text = DISCLAIMER_STRIP.sub(" ", text)  # remove the standing disclaimer sentence first
    for pat in PROHIBITED_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(
                f"prohibited advice/determination language detected: {m.group(0)!r} "
                f"(R1 is informational only — no coverage/eligibility/claim decision or advice)")

    if not DISCLAIMER_RE.search(str(s.get("narrative", "")) + " " + str(s.get("disclaimer", ""))):
        errors.append("missing standing disclaimer: 'Informational explanation only; not a "
                      "coverage determination, claim decision, or insurance/legal advice.'")

    return errors


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        fixture = Path(__file__).resolve().parents[1] / "evals" / "files" / "explanation_example.json"
        s = json.loads(fixture.read_text(encoding="utf-8"))
    elif argv:
        s = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        s = json.loads(sys.stdin.read())
    errors = validate(s)
    for e in errors:
        print("ERROR", e)
    print(f"output validation: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
