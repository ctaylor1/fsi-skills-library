#!/usr/bin/env python3
"""Deterministic output validation for composite-account-membership-checker.

Validates the exception-queue pack (the calculate_or_transform core + a narrative) before it
is presented to or delivered for a performance analyst. This is the R3 prohibited-decision
screen: it fails closed if the pack asserts or recommends a prohibited action (changing a
composite, its membership, the methodology, or reported performance; recalculating returns;
closing/filing/writing a system of record) instead of staging evidence for human
adjudication.

Checks:
  1. Every exception carries >= 1 cited evidence row and a rule citation (rule_id + version).
  2. queue_priority equals the deterministic mapping from the exception-type set.
  3. No prohibited membership/methodology/performance/closure/filing language anywhere in the
     narrative, notes, or exception reasons.
  4. Every exception status is "for_review" (never resolved/closed/applied/corrected/posted).
  5. human_adjudication_required is true whenever any exception is present.
  6. The standing disclaimer is present.

Usage:
  python validate_output.py queue_pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

# Must stay identical to calculate_or_transform.expected_queue_priority.
ESCALATORS = {"improper_inclusion", "stale_inclusion", "unassigned_discretionary"}
DISCLAIMER = ("Composite-membership exceptions are evidence for analyst adjudication only; "
             "this skill does not modify composites, methodology, or reported performance.")
PROHIBITED_STATUS = {"resolved", "closed", "applied", "corrected", "posted", "filed", "approved"}

# Prohibited-decision / action language an R3 evidence queue must never assert or recommend.
PROHIBITED_PATTERNS = [
    r"\breassigned\b", r"\brestated\b", r"\brecalculated\b", r"\brecomputed\b",
    r"changed the composite", r"change the composite", r"updated the composite",
    r"corrected the composite", r"modified the composite",
    r"added .{0,50}to the .{0,25}composite", r"removed .{0,50}from the .{0,25}composite",
    r"composite membership (has been |was )?(updated|changed|corrected)",
    r"changed the methodology", r"updated the methodology",
    r"changed the (reported )?performance", r"performance (has been |was )?restated",
    r"case closed", r"exception closed", r"marked (as )?resolved",
    r"posted to the system of record", r"wrote to the system of record",
    r"approved and applied", r"applied the (change|correction)", r"\bfiled the\b",
]


def expected_queue_priority(exception_types: list) -> str:
    if not exception_types:
        return "None"
    if (ESCALATORS & set(exception_types)) or len(exception_types) >= 3:
        return "Elevated"
    return "Review"


def validate(pack: dict) -> list:
    errors: list = []
    exceptions = pack.get("exceptions") or []

    for e in exceptions:
        ref = e.get("case_ref") or e.get("portfolio_id") or "?"
        ev = e.get("evidence") or []
        if not ev:
            errors.append(f"exception {ref} has no evidence")
        for row in ev:
            if not str(row.get("citation") or "").strip():
                errors.append(f"exception {ref} evidence row missing citation")
        rule = e.get("rule") or {}
        if not (str(rule.get("rule_id") or "").strip() and str(rule.get("rule_version") or "").strip()):
            errors.append(f"exception {ref} missing rule_id/rule_version citation")
        status = str(e.get("status") or "").lower()
        if status != "for_review":
            errors.append(f"exception {ref} status {status!r} is not 'for_review' (R3 never resolves/closes/applies)")
        elif status in PROHIBITED_STATUS:
            errors.append(f"exception {ref} status {status!r} implies a prohibited disposition")

    exc_types = pack.get("exception_types")
    if exc_types is None:
        exc_types = [e.get("exception_type") for e in exceptions]
    exp = expected_queue_priority(exc_types)
    if pack.get("queue_priority") != exp:
        errors.append(f"queue_priority {pack.get('queue_priority')!r} != deterministic {exp!r} for {exc_types}")

    if exceptions and not pack.get("human_adjudication_required"):
        errors.append("exceptions present but human_adjudication_required is not true")

    # Scan narrative + notes + exception reasons — but NOT the disclaimer field.
    text = " ".join([str(pack.get("narrative", "")), str(pack.get("notes", ""))]
                    + [str(e.get("reason", "")) for e in exceptions])
    for pat in PROHIBITED_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"prohibited decision/action language detected: {m.group(0)!r} "
                          f"(R3 evidences and routes; it never changes membership/methodology/performance)")

    disclaimer_scope = (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower()
    if DISCLAIMER.lower() not in disclaimer_scope:
        errors.append("missing standing disclaimer text")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "queue_pack_example.json"
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
