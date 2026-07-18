#!/usr/bin/env python3
"""Deterministic output validation for knowledge-answer-composer.

Confirms a composed answer is fully source-grounded, built only from approved, in-effect,
jurisdiction-matched knowledge, and free of advice / recommendation / coverage-eligibility-
determination language BEFORE it is presented or delivered.

Checks:
  1. Every claim carries a non-empty citation and a source_id present in sources_used.
  2. Every claim.text appears verbatim in answer_text (the narrative is grounded in claims).
  3. An answered response has >=1 claim; an unanswered one states it cannot be answered.
  4. Every source in sources_used is 'approved', in effect as of as_of_date (effective <=
     as_of, and no expiry or expiry >= as_of) and jurisdiction-matched — no stale, draft, or
     out-of-jurisdiction basis.
  5. No advice / recommendation / coverage-eligibility-fraud determination language (the R1
     tier guardrail): fail closed on any hit.
  6. The standing informational-only disclaimer is present.

Output schema (JSON):
{
  "answer_id","request_id","as_of_date","jurisdiction","unanswered"(bool),
  "claims":[{"text","citation","source_id"}],
  "sources_used":[{"source_id","type","status","effective_date","expiry_date"(opt),
                   "jurisdiction"(opt),"ref"}],
  "answer_text":"...","uncertainty"(opt),"notes"(opt),"disclaimer"(opt)
}

Usage:
  python validate_output.py answer.json
  python validate_output.py --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# Advice / recommendation and coverage-eligibility-determination phrasing. Targets the
# ASSISTANT making a call about THIS customer; avoids matching neutral quoted policy text
# or the standing disclaimer ("coverage, eligibility, or account determination").
ADVICE_PATTERNS = [
    r"\byou should\b", r"\byou (ought to|might want to|may want to)\b",
    r"\bwe (recommend|suggest|advise)\b", r"\bwe'd (recommend|suggest)\b",
    r"\bi (recommend|suggest|would suggest|advise|'d suggest)\b",
    r"\brecommend(s|ed|ing)?\b",
    r"\bbest (option|choice|account|product|plan|card|fit)\b",
    r"\byou'd be better off\b", r"\bi'd (go with|pick|choose)\b",
    r"\byou (are|'re) eligible\b", r"\byou qualify\b",
    r"\byou (are|'re) (pre-?)?approved\b",
    r"\byour (claim|dispute|case|account|application) (is|has been|will be|would be) "
    r"(approved|denied|declined|upheld|covered|rejected)\b",
    r"\bthis (is|would be) covered\b", r"\byou (are|'re) covered\b",
    r"\bwe (will|can|'ll) (cover|refund|approve|waive|reimburse|credit)\b",
    r"\b(buy|sell|invest in) (this|these|it|now)\b",
]
DISCLAIMER_RE = re.compile(r"informational answer.*not advice.*determination", re.I | re.S)


def validate(a: dict) -> list[str]:
    errors: list[str] = []
    as_of = str(a.get("as_of_date", ""))
    if not DATE_RE.match(as_of):
        errors.append(f"as_of_date must be YYYY-MM-DD, got {a.get('as_of_date')!r}")
    juris = a.get("jurisdiction")
    unanswered = bool(a.get("unanswered"))
    answer_text = str(a.get("answer_text", ""))
    claims = a.get("claims") or []
    sources_used = a.get("sources_used") or []
    su_index = {s.get("source_id"): s for s in sources_used}

    if not answer_text.strip():
        errors.append("answer_text is empty — provide a plain-language answer or an explicit cannot-answer statement")

    if not unanswered and not claims:
        errors.append("no claims — an answered response must ground every statement in a cited claim "
                      "(or set unanswered=true and route to a human)")

    for c in claims:
        cid = c.get("source_id", "?")
        text = str(c.get("text", "")).strip()
        if not text:
            errors.append(f"claim (source {cid}): empty text")
        if not str(c.get("citation", "")).strip():
            errors.append(f"claim (source {cid}): missing citation")
        if not c.get("source_id"):
            errors.append("claim: missing source_id")
        elif c["source_id"] not in su_index:
            errors.append(f"claim cites source_id {c['source_id']!r} not present in sources_used")
        if text and text not in answer_text:
            errors.append(f"claim text not found in answer_text (ungrounded narrative): {text[:60]!r}")

    for s in sources_used:
        sid = s.get("source_id", "?")
        st = s.get("status")
        if st != "approved":
            errors.append(f"source {sid}: status {st!r} is not 'approved' — answers use approved knowledge only")
        eff = str(s.get("effective_date", ""))
        if not DATE_RE.match(eff):
            errors.append(f"source {sid}: effective_date must be YYYY-MM-DD, got {eff!r}")
        elif DATE_RE.match(as_of) and eff > as_of:
            errors.append(f"source {sid}: not yet effective (effective {eff} > as_of {as_of})")
        exp = s.get("expiry_date")
        if exp and DATE_RE.match(str(exp)) and DATE_RE.match(as_of) and str(exp) < as_of:
            errors.append(f"source {sid}: expired (expiry {exp} < as_of {as_of}) — stale basis")
        sj = s.get("jurisdiction")
        if sj and juris and sj != juris:
            errors.append(f"source {sid}: jurisdiction {sj} != answer {juris} — out-of-jurisdiction basis")

    scan = " ".join([answer_text, str(a.get("uncertainty", "")), str(a.get("notes", ""))]
                    + [str(c.get("text", "")) for c in claims])
    for pat in ADVICE_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"prohibited advice/determination language detected: {m.group(0)!r} "
                          f"(R1 composes source-grounded answers only; no advice or determinations)")

    disc = answer_text + " " + str(a.get("disclaimer", ""))
    if not DISCLAIMER_RE.search(disc):
        errors.append("missing standing disclaimer: 'Informational answer composed from approved sources "
                      "...; not advice and not a coverage, eligibility, or account determination.'")

    return errors


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        fixture = Path(__file__).resolve().parents[1] / "evals" / "files" / "answer_example.json"
        a = json.loads(fixture.read_text(encoding="utf-8"))
    elif argv:
        a = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        a = json.loads(sys.stdin.read())
    errors = validate(a)
    for e in errors:
        print("ERROR", e)
    print(f"output validation: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
