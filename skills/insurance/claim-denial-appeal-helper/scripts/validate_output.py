#!/usr/bin/env python3
"""Deterministic output validation for claim-denial-appeal-helper.

Validates the final appeal package (the calculate_or_transform core + a narrative) before it
is presented or delivered. This is the R2 tier guardrail: the package must be administrative
support, never legal advice, a coverage/eligibility determination, a guaranteed outcome, or a
filed appeal. Checks:
  1. Every drafted argument point is evidence-backed — a reason with argument_points must
     have >= 1 evidence_present row, and every evidence_present row must carry a citation
     (no unsupported/unapproved claims).
  2. Deterministic deadline + readiness: appeal_deadline == denial_date + appeal_window_days,
     days_remaining/deadline_status recompute from as_of, and readiness maps from the gaps.
  3. No prohibited language: no legal advice, no coverage/eligibility determination, no
     guaranteed outcome, no "we filed the appeal" (narrative + notes + argument text).
  4. The standing disclaimer is present.
  5. The draft is marked human_review_required (external-delivery approval gate).
  6. When evidence gaps exist, outstanding_evidence prompts are present (gap disclosure).

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from datetime import datetime, timedelta
from pathlib import Path

DISCLAIMER = ("Administrative appeal support only; not legal advice and not a coverage "
              "determination. The insurer or an independent external reviewer decides the "
              "appeal; no appeal has been filed on the member's behalf.")
DEFAULT_DUE_SOON_DAYS = 30

# Assertions an R2 administrative-support skill must never make. Kept specific so legitimate
# neutral wording ("seeks to overturn the denial", "not legal advice") does not trip.
PROHIBITED_PATTERNS = [
    # legal advice / litigation posture
    r"\byou should sue\b", r"\bfile (a )?lawsuit\b", r"\bsue (the|your) (insurer|plan|carrier|company)\b",
    r"\byou are legally entitled\b", r"\blegally obligated to pay\b", r"\bbad faith\b",
    r"\bthe denial is (invalid|illegal|unlawful)\b", r"\bthe denial was (wrong|illegal|unlawful)\b",
    # coverage / eligibility determination (the insurer's or external reviewer's call)
    r"\bthe (claim|service) is covered\b", r"\bcoverage applies\b", r"\bthe insurer must pay\b",
    r"\byou are eligible for coverage\b", r"\bwe have determined\b", r"\bthe claim will be paid\b",
    # guaranteed outcome
    r"\bguarantee[ds]?\b", r"\bcertain to (win|succeed|be overturned)\b",
    r"\byou will win\b", r"\bwe will win\b",
    # filing on the member's behalf
    r"\bwe (have )?filed\b", r"\bappeal (has been|was) (filed|submitted)\b",
    r"\bsubmitted the appeal\b", r"\bfiled on (your|the member'?s) behalf\b",
]


def _parse_date(s: str) -> datetime:
    return datetime.strptime(str(s)[:10], "%Y-%m-%d")


def _expected_readiness(pack: dict) -> str:
    for a in pack.get("appeal_arguments") or []:
        if a.get("evidence_gaps"):
            return "gaps_present"
    return "ready_to_draft"


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    args = pack.get("appeal_arguments") or []

    # 1. Evidence-backed argument points (no unsupported claims).
    for a in args:
        code = a.get("reason_code", "?")
        points = a.get("argument_points") or []
        ev = a.get("evidence_present") or []
        if points and not ev:
            errors.append(f"unsupported argument for {code}: argument_points present with no cited evidence")
        for row in ev:
            if not str(row.get("citation") or "").strip():
                errors.append(f"evidence row for {code} missing citation")

    # 2. Deterministic deadline + readiness.
    try:
        denial = _parse_date(pack["denial_date"])
        window = int(pack["appeal_window_days"])
        as_of = _parse_date(pack["as_of"])
        due_soon = int(pack.get("due_soon_days", DEFAULT_DUE_SOON_DAYS))
        exp_deadline = (denial + timedelta(days=window)).strftime("%Y-%m-%d")
        exp_remaining = (denial + timedelta(days=window) - as_of).days
        exp_status = "past_due" if exp_remaining < 0 else ("due_soon" if exp_remaining <= due_soon else "open")
        if pack.get("appeal_deadline") != exp_deadline:
            errors.append(f"appeal_deadline {pack.get('appeal_deadline')!r} != deterministic {exp_deadline!r}")
        if pack.get("days_remaining") != exp_remaining:
            errors.append(f"days_remaining {pack.get('days_remaining')!r} != deterministic {exp_remaining}")
        if pack.get("deadline_status") != exp_status:
            errors.append(f"deadline_status {pack.get('deadline_status')!r} != deterministic {exp_status!r}")
    except (KeyError, ValueError, TypeError):
        errors.append("cannot verify deadline: denial_date, appeal_window_days, and as_of are required")

    exp_readiness = _expected_readiness(pack)
    if pack.get("readiness") != exp_readiness:
        errors.append(f"readiness {pack.get('readiness')!r} != deterministic {exp_readiness!r} from evidence gaps")

    # 3. Prohibited-language screen over free text (NOT the disclaimer field).
    text_parts = [str(pack.get("narrative", "")), str(pack.get("notes", ""))]
    for a in args:
        text_parts.append(str(a.get("explanation", "")))
        text_parts.extend(str(p) for p in (a.get("argument_points") or []))
    text = " ".join(text_parts)
    for pat in PROHIBITED_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"prohibited-language detected: {m.group(0)!r} (R2 supports; it does not advise, determine, guarantee, or file)")

    # 4. Standing disclaimer present.
    combined = (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower()
    if DISCLAIMER.lower() not in combined:
        errors.append("missing standing disclaimer text")

    # 5. External-delivery approval gate.
    if pack.get("human_review_required") is not True:
        errors.append("draft not marked human_review_required (external-delivery approval gate)")

    # 6. Gap disclosure.
    has_gaps = any(a.get("evidence_gaps") for a in args)
    if has_gaps and not (pack.get("outstanding_evidence")):
        errors.append("evidence gaps present but no outstanding_evidence prompts included")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "appeal_pack_example.json"
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
