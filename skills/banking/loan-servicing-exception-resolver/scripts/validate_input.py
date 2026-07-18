#!/usr/bin/env python3
"""Deterministic input validation for loan-servicing-exception-resolver.

Validates a confirmed servicing exception + proposed remedy before planning. Fails closed
on structural problems or a remedy that is not permissible / over limit / missing evidence.

Input schema (JSON): see references/domain-rules.md. Key fields:
  exception_id, loan_id, type, catalog_version, evidence{...}, proposed_remedy{action,amount,target}

Usage: python validate_input.py exception.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

# Permissible-remedy catalog (default; deployment supplies a versioned catalog).
CATALOG = {
    "misapplied_payment": {"action": "reallocate_payment", "limit": 25000, "reversible": True,
                           "approver": "servicing-supervisor", "evidence": ["payment_record", "correct_allocation"]},
    "late_fee_in_error": {"action": "reverse_fee", "limit": 500, "reversible": True,
                          "approver": "servicing-specialist", "evidence": ["fee_record", "error_evidence"]},
    "escrow_shortage_miscalc": {"action": "adjust_escrow", "limit": 5000, "reversible": True,
                                "approver": "escrow-analyst", "evidence": ["escrow_analysis", "recomputation"]},
    "duplicate_payment": {"action": "refund_duplicate", "limit": 25000, "reversible": True,
                          "approver": "servicing-supervisor", "evidence": ["payment_record_1", "payment_record_2", "duplication_proof"]},
}
REQUIRED_TOP = ("exception_id", "loan_id", "type", "proposed_remedy")


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    etype = doc["type"]
    cat = CATALOG.get(etype)
    if not cat:
        errors.append(f"exception type {etype!r} not in permissible-remedy catalog — escalate (out of scope)")
        return errors, warnings

    rem = doc.get("proposed_remedy") or {}
    if rem.get("action") != cat["action"]:
        errors.append(f"proposed action {rem.get('action')!r} != catalog action {cat['action']!r} for {etype}")
    amt = rem.get("amount")
    try:
        amt = float(amt)
    except (TypeError, ValueError):
        errors.append("proposed_remedy.amount is not numeric")
        amt = None
    if amt is not None:
        if amt <= 0:
            errors.append("proposed_remedy.amount must be > 0")
        if amt > cat["limit"]:
            errors.append(f"amount {amt} exceeds authority limit {cat['limit']} for {etype} — escalate (out of scope)")
    if not rem.get("target"):
        errors.append("proposed_remedy.target is required")
    if not cat["reversible"]:
        errors.append(f"remedy for {etype} is not reversible — out of scope for auto-planning")

    ev = doc.get("evidence") or {}
    missing_ev = [e for e in cat["evidence"] if not ev.get(e)]
    if missing_ev:
        errors.append(f"missing required evidence for {etype}: {', '.join(missing_ev)}")

    if not doc.get("catalog_version"):
        warnings.append("no catalog_version — record the versioned catalog used for reproducibility")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "exception_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    errors, warnings = validate(doc)
    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"input validation: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
