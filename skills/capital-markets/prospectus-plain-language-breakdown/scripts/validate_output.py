#!/usr/bin/env python3
"""Deterministic output validation for prospectus-plain-language-breakdown.

Confirms the plain-language breakdown is complete, fully page-cited, and free of
advice/solicitation language BEFORE it is presented or delivered. This is the R2 guardrail
screen: an informational/explanatory skill may explain a prospectus, but must never
recommend, solicit, judge suitability, or opine on the offering.

Checks (each failure returns a non-zero exit):
  1. Completeness  - every required topic (fees, strategy, liquidity, conflicts, risks,
     obligations) is either covered as a section OR explicitly recorded in data_gaps.
  2. Citation cov. - every covered section carries a non-empty page citation; source_pages,
     where present, are positive integers.
  3. No advice     - narrative and every section are free of advice/recommendation/
     solicitation phrasing.
  4. Disclaimer    - the standing informational-only disclaimer is present.

Output schema (JSON):
{
  "breakdown_id","document_id","issuer","instrument","document_type","effective_date",
  "jurisdiction",
  "sections":[{"topic","plain_language","citation","source_pages"(opt)}],
  "data_gaps":[ "conflicts: not disclosed in summary prospectus; see SAI", ... ],
  "narrative":"...",
  "disclaimer":"Plain-language summary only; not investment advice, ... "
}

Usage:
  python validate_output.py breakdown.json
  python validate_output.py --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

REQUIRED_TOPICS = ("fees", "strategy", "liquidity", "conflicts", "risks", "obligations")

ADVICE_PATTERNS = [
    r"\brecommend(s|ed|ing|ation)?\b",
    r"\bshould (invest|buy|subscribe|purchase|sell|redeem|hold|consider|avoid|allocate)\b",
    r"\byou (should|ought to|must|might want to)\b",
    r"\bwe (suggest|advise|recommend|encourage)\b",
    r"\bconsider (investing|subscribing|buying|purchasing)\b",
    r"\b(buy|subscribe|invest|purchase) (now|today|this|here)\b",
    r"\b(good|bad|great|attractive|poor|solid|strong) investment\b",
    r"\b(is|looks|seems) (a good|a bad|attractive|expensive|cheap|risky|safe|suitable|unsuitable|appropriate)\b",
    r"\bwell[- ]diversified\b",
    r"\bguaranteed (return|returns|income|profit|profits|gains)\b",
    r"\bwill (outperform|beat|rise|grow|appreciate|increase in value)\b",
    r"\bgreat (opportunity|deal|buy)\b",
    r"\b(low|high)[- ]risk (choice|option|investment|pick)\b",
    r"\bworth (it|buying|investing|subscribing)\b",
    r"\bsuitable for (you|your)\b",
    r"\bbest (fund|option|choice|investment|pick)\b",
]

# Standing disclaimer must state both that it is not advice and to read the full prospectus.
NOT_ADVICE_RE = re.compile(r"not\s+(investment\s+)?advice", re.I)
READ_FULL_RE = re.compile(r"read the (full |entire )?prospectus", re.I)


def _texts(s: dict):
    """Yield every human-readable string in the breakdown for the advice scan."""
    yield str(s.get("narrative", ""))
    yield str(s.get("notes", ""))
    for sec in s.get("sections") or []:
        yield str(sec.get("plain_language", ""))
        yield str(sec.get("heading", ""))


def _flagged_gap(topic: str, gaps) -> bool:
    tre = re.compile(rf"\b{re.escape(topic)}\b", re.I)
    for g in gaps:
        if tre.search(str(g)):
            return True
    return False


def validate(s: dict) -> list[str]:
    errors: list[str] = []
    sections = s.get("sections") or []
    if not sections:
        return ["breakdown missing 'sections'"]

    gaps = s.get("data_gaps") or []

    # 1 + 2: per-section citation coverage; build covered-topic set.
    covered: set[str] = set()
    for sec in sections:
        topic = sec.get("topic") or "?"
        pl = (sec.get("plain_language") or "").strip()
        cite = (sec.get("citation") or "").strip()
        if not pl:
            errors.append(f"section '{topic}': empty plain_language")
        if not cite:
            errors.append(f"section '{topic}': missing page citation")
        sp = sec.get("source_pages")
        if sp is not None:
            if not isinstance(sp, list) or not sp:
                errors.append(f"section '{topic}': source_pages must be a non-empty list when present")
            else:
                for p in sp:
                    if not isinstance(p, int) or isinstance(p, bool) or p < 1:
                        errors.append(f"section '{topic}': source_pages must be positive integers, got {p!r}")
        if pl and cite:
            covered.add(topic)

    # 1: completeness - every required topic covered or flagged as a gap.
    for t in REQUIRED_TOPICS:
        if t not in covered and not _flagged_gap(t, gaps):
            errors.append(
                f"required topic '{t}' is neither covered with a citation nor recorded in data_gaps "
                f"(completeness failure)")

    # 3: no advice / no solicitation.
    blob = "\n".join(_texts(s))
    for pat in ADVICE_PATTERNS:
        m = re.search(pat, blob, re.I)
        if m:
            errors.append(f"advice/solicitation language detected: {m.group(0)!r} (R2 is informational only)")

    # 4: standing disclaimer.
    disc = str(s.get("narrative", "")) + " " + str(s.get("disclaimer", ""))
    if not (NOT_ADVICE_RE.search(disc) and READ_FULL_RE.search(disc)):
        errors.append(
            "missing standing disclaimer: 'Plain-language summary only; not investment advice, "
            "a recommendation, a solicitation, or an offer. Read the full prospectus before investing.'")

    return errors


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        fixture = Path(__file__).resolve().parents[1] / "evals" / "files" / "breakdown_example.json"
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
