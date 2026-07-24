#!/usr/bin/env python3
"""Deterministic output validation for order-allocation-validator.

Enforces the R3 guardrails before the exception packet is presented:
  1. allocated_qty ties to executed_qty, or quantity_break is flagged.
  2. Every exception carries a non-empty citation.
  3. suggested_disposition is review-only (clean | exceptions-for-review).
  4. No allocation-decision / amendment / booking / compliance-certification language.
  5. Standing disclaimer present.

Usage: python validate_output.py packet.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ALLOWED_DISPOSITIONS = {"clean", "exceptions-for-review"}
DISCLAIMER_RE = re.compile(r"not an allocation decision.*(no order has been allocated|not.*certification)", re.I)
DECISION_PATTERNS = [
    r"\b(we|i) (have )?(allocated|re-?allocated|amended|booked)\b",
    r"\bre-?allocate the order\b", r"\bamend(ed)? the order\b",
    r"\bbook(ed)? the allocation\b", r"\bapprov(e|ed) (the )?allocation\b",
    r"\ballocation is compliant\b", r"\bcertif(y|ied)\b.{0,30}complian",
]


def validate(p: dict) -> list[str]:
    errors = []
    executed = p.get("executed_qty")
    allocated = p.get("allocated_qty")
    if executed is not None and allocated is not None:
        if abs(allocated - executed) > 1e-6 and not p.get("quantity_break"):
            errors.append(f"allocated_qty {allocated} != executed_qty {executed} but quantity_break not flagged")
    for e in p.get("exceptions") or []:
        if not (e.get("citation") or "").strip():
            errors.append(f"exception {e.get('rule','?')}/{e.get('account_id','?')}: missing citation")
    if p.get("suggested_disposition") not in ALLOWED_DISPOSITIONS:
        errors.append(f"suggested_disposition {p.get('suggested_disposition')!r} not review-only {sorted(ALLOWED_DISPOSITIONS)}")

    scan = json.dumps({k: v for k, v in p.items() if k != "disclaimer"}) + " " + str(p.get("narrative", ""))
    for pat in DECISION_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"allocation-decision/amendment language detected: {m.group(0)!r} (R3 evidences, does not decide/act)")
    if not DISCLAIMER_RE.search(str(p.get("disclaimer", "")) + " " + str(p.get("narrative", ""))):
        errors.append("missing standing disclaimer (evidence-only / no order allocated or booked)")
    return errors


def main(argv):
    if "--selftest" in argv:
        pth = Path(__file__).resolve().parents[1] / "evals" / "files" / "packet_example.json"
        p = json.loads(pth.read_text(encoding="utf-8"))
    elif argv:
        p = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        p = json.loads(sys.stdin.read())
    errors = validate(p)
    for e in errors:
        print("ERROR", e)
    print(f"output validation: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
