#!/usr/bin/env python3
"""Deterministic output validation for customer-interaction-summarizer.

Confirms the interaction summary is complete, fully cited, plain-language, and free of
advice / next-best-action / determination language BEFORE it is presented or delivered.

Checks:
  1. Required header fields present (summary_id, interaction_id, channel,
     interaction_date, overall_sentiment).
  2. overall_sentiment is one of the allowed labels.
  3. key_points is non-empty; every item in key_points / commitments / disclosures /
     open_actions carries a non-empty citation (source fidelity + coverage).
  4. Customer reference and narrative contain no unmasked identifier (7+ digit run).
  5. Narrative / assessment text contains no advice, next-best-action, or determination
     phrasing (R1 is informational only). Structured, attributed commitments/disclosures
     are records of what was said and are NOT scanned.
  6. The standing informational-only disclaimer is present.

Summary schema (JSON):
{
  "summary_id","interaction_id","customer_ref","channel","interaction_date",
  "overall_sentiment":"positive|neutral|negative|mixed",
  "key_points":[{"text","citation"}],
  "commitments":[{"text","owner","citation"}],
  "disclosures":[{"text","citation"}],
  "open_actions":[{"text","owner","citation"}],
  "data_gaps":[...], "narrative":"...", "disclaimer":"..."
}

Usage:
  python validate_output.py summary.json
  python validate_output.py --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ALLOWED_SENTIMENT = {"positive", "neutral", "negative", "mixed"}
REQUIRED_TOP = ("summary_id", "interaction_id", "channel", "interaction_date", "overall_sentiment")
CITED_LISTS = ("key_points", "commitments", "disclosures", "open_actions")
DIGIT_RUN_RE = re.compile(r"\d{7,}")

ADVICE_PATTERNS = [
    r"\brecommend(s|ed|ing|ation)?\b", r"\bwe (suggest|advise|recommend)\b",
    r"\byou (should|ought to|must|might want to)\b",
    r"\bthe (agent|customer|rep|advisor) should\b",
    r"\bnext[- ]best[- ]action\b", r"\bbest (option|course of action|next step)\b",
    r"\bshould (offer|call|escalate|refund|waive|approve|deny|reduce|increase|consider)\b",
    r"\bi (suggest|advise|recommend)\b", r"\bproactively offer\b",
]
DETERMINATION_PATTERNS = [
    r"\bcomplaint (is|was) (upheld|justified|unjustified|rejected|valid|invalid|warranted)\b",
    r"\b(uphold|reject|deny) (the|this) complaint\b",
    r"\bthis (is|constitutes) fraud\b", r"\bfraud (is )?(confirmed|established)\b",
    r"\bcustomer is (a |clearly )?vulnerab\w+\b",
    r"\b(is|are|not|isn'?t) eligible\b", r"\bineligible\b",
    r"\b(coverage|claim|refund|benefit) (is )?(approved|denied|granted|valid|invalid)\b",
    r"\bwe (will|shall) (waive|refund|credit|approve|deny|reimburse)\b",
    r"\bwas (compliant|non-?compliant)\b",
]
DISCLAIMER_RE = re.compile(
    r"informational summary only.*not advice and not a determination", re.I | re.S)


def validate(s: dict) -> list[str]:
    errors: list[str] = []

    for k in REQUIRED_TOP:
        if k not in s or s.get(k) in (None, ""):
            errors.append(f"missing header field '{k}'")

    sent = s.get("overall_sentiment")
    if sent is not None and sent not in ALLOWED_SENTIMENT:
        errors.append(f"overall_sentiment {sent!r} not in {sorted(ALLOWED_SENTIMENT)}")

    key_points = s.get("key_points") or []
    if not key_points:
        errors.append("key_points is empty — a summary must state at least one cited key point")

    for lst in CITED_LISTS:
        for i, item in enumerate(s.get(lst) or []):
            if not isinstance(item, dict):
                errors.append(f"{lst}[{i}]: must be an object with text + citation")
                continue
            if not str(item.get("text", "")).strip():
                errors.append(f"{lst}[{i}]: missing text")
            if not str(item.get("citation", "")).strip():
                errors.append(f"{lst}[{i}]: missing citation")

    cust = str(s.get("customer_ref", ""))
    if DIGIT_RUN_RE.search(cust):
        errors.append(f"customer_ref {cust!r} contains an unmasked identifier (7+ digit run) — mask to last 4")

    narrative = str(s.get("narrative", ""))
    assessment = str(s.get("assessment", "")) + " " + str(s.get("notes", ""))
    if DIGIT_RUN_RE.search(narrative):
        errors.append("narrative contains an unmasked identifier (7+ digit run)")

    scan = narrative + " " + assessment
    for pat in ADVICE_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"advice/recommendation language detected: {m.group(0)!r} (R1 is informational only)")
    for pat in DETERMINATION_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"determination language detected: {m.group(0)!r} (route to the adjudicating skill)")

    if not DISCLAIMER_RE.search(narrative + " " + str(s.get("disclaimer", ""))):
        errors.append("missing standing disclaimer: 'Informational summary only; not advice and not a determination. ...'")

    return errors


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        fixture = Path(__file__).resolve().parents[1] / "evals" / "files" / "summary_example.json"
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
