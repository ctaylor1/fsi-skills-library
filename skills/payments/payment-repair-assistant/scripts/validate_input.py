#!/usr/bin/env python3
"""Deterministic input validation for payment-repair-assistant.

Validates an approved payment-exception / investigation case + proposed repair before
planning. Fails closed on structural problems, a repair that is not permissible / over the
authority limit / missing evidence, or a resubmission whose sanctions screening is not
cleared. Read-only: it never resubmits, releases, returns, or cancels a payment.

Input schema (JSON): see references/domain-rules.md. Key fields:
  case_id, payment_id, type, catalog_version, rail, end_to_end_id,
  screening{status,...}, evidence{...}, beneficiary{...},
  proposed_repair{action, amount, currency, field, new_value, target, rail}

Usage: python validate_input.py case.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

# Permissible-repair catalog (default; deployment supplies a versioned catalog).
# screening: True  -> resubmission/release is blocked unless sanctions screening is cleared.
CATALOG = {
    "invalid_beneficiary_detail": {
        "action": "repair_and_resubmit", "limit": 100000, "reversible": True,
        "approver": "payments-repair-supervisor", "screening": True,
        "evidence": ["original_message", "corrected_field", "verification_source"]},
    "missing_remittance_info": {
        "action": "repair_and_resubmit", "limit": 50000, "reversible": True,
        "approver": "payments-repair-specialist", "screening": True,
        "evidence": ["original_message", "remittance_source"]},
    "missing_purpose_code": {
        "action": "repair_and_resubmit", "limit": 50000, "reversible": True,
        "approver": "payments-repair-specialist", "screening": True,
        "evidence": ["original_message", "purpose_code_source"]},
    "held_screening_cleared": {
        "action": "release_and_resubmit", "limit": 100000, "reversible": True,
        "approver": "payments-repair-supervisor", "screening": True,
        "evidence": ["original_message", "screening_disposition"]},
    "unrecoverable_reject": {
        "action": "return_to_originator", "limit": 100000, "reversible": True,
        "approver": "payments-repair-supervisor", "screening": False,
        "evidence": ["original_message", "reject_reason"]},
}
CLEARED_SCREENING = ("clear", "false_positive_cleared")
REQUIRED_TOP = ("case_id", "payment_id", "type", "end_to_end_id", "screening", "proposed_repair")


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
        errors.append(f"exception type {etype!r} not in permissible-repair catalog — escalate (out of scope)")
        return errors, warnings

    rem = doc.get("proposed_repair") or {}
    if rem.get("action") != cat["action"]:
        errors.append(f"proposed action {rem.get('action')!r} != catalog action {cat['action']!r} for {etype}")

    amt = rem.get("amount")
    try:
        amt = float(amt)
    except (TypeError, ValueError):
        errors.append("proposed_repair.amount is not numeric")
        amt = None
    if amt is not None:
        if amt <= 0:
            errors.append("proposed_repair.amount must be > 0")
        if amt > cat["limit"]:
            errors.append(f"amount {amt} exceeds repair authority limit {cat['limit']} for {etype} — escalate (out of scope)")

    if not rem.get("target"):
        errors.append("proposed_repair.target is required")
    if not cat["reversible"]:
        errors.append(f"repair for {etype} is not reversible — out of scope for auto-planning")
    if not str(doc.get("end_to_end_id", "")).strip():
        errors.append("end_to_end_id is required (idempotency / duplicate-payment guard)")

    # Compliance gate: a resubmission/release must not proceed on an uncleared screening hit.
    scr = doc.get("screening") or {}
    if cat["screening"]:
        status = scr.get("status")
        if status not in CLEARED_SCREENING:
            errors.append(f"sanctions screening not cleared (status={status!r}) for {etype} — "
                          f"resubmission blocked; route to sanctions/compliance (out of scope)")

    ev = doc.get("evidence") or {}
    missing_ev = [e for e in cat["evidence"] if not ev.get(e)]
    if missing_ev:
        errors.append(f"missing required evidence for {etype}: {', '.join(missing_ev)}")

    if not rem.get("currency"):
        warnings.append("no proposed_repair.currency — record the settlement currency for the amount")
    if not doc.get("catalog_version"):
        warnings.append("no catalog_version — record the versioned catalog used for reproducibility")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "case_example.json"
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
