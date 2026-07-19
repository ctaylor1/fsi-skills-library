#!/usr/bin/env python3
"""Deterministic input validation for trade-break-resolver.

Validates a confirmed trade break + proposed repair before planning. Fails closed on
structural problems or a repair that is not permissible / over limit / missing evidence.

Input schema (JSON): see references/domain-rules.md. Key fields:
  break_id, trade_id, type, catalog_version, evidence{...},
  proposed_repair{action, amount, target[, source]}

Usage: python validate_input.py break.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

# Permissible-repair catalog (default; deployment supplies a versioned catalog).
# "amount" is the economic value of the repair (notional moved/adjusted or economic
# difference), compared against the per-type authority limit.
CATALOG = {
    "mis_booked_account": {"action": "rebook_trade", "limit": 5000000, "reversible": True,
                           "approver": "trade-support-supervisor",
                           "evidence": ["firm_booking", "counterparty_confirmation", "correct_booking_target"]},
    "quantity_mismatch": {"action": "amend_quantity", "limit": 5000000, "reversible": True,
                          "approver": "trade-support-supervisor",
                          "evidence": ["firm_booking", "counterparty_confirmation", "matched_trade_key"]},
    "price_mismatch": {"action": "amend_price", "limit": 250000, "reversible": True,
                       "approver": "trade-support-specialist",
                       "evidence": ["firm_booking", "counterparty_confirmation", "agreed_price_evidence"]},
    "duplicate_booking": {"action": "cancel_trade", "limit": 5000000, "reversible": True,
                          "approver": "trade-support-supervisor",
                          "evidence": ["firm_booking_1", "firm_booking_2", "duplication_proof"]},
}
REQUIRED_TOP = ("break_id", "trade_id", "type", "proposed_repair")


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    btype = doc["type"]
    cat = CATALOG.get(btype)
    if not cat:
        errors.append(f"break type {btype!r} not in permissible-repair catalog — escalate (out of scope)")
        return errors, warnings

    rep = doc.get("proposed_repair") or {}
    if rep.get("action") != cat["action"]:
        errors.append(f"proposed action {rep.get('action')!r} != catalog action {cat['action']!r} for {btype}")
    amt = rep.get("amount")
    try:
        amt = float(amt)
    except (TypeError, ValueError):
        errors.append("proposed_repair.amount is not numeric")
        amt = None
    if amt is not None:
        if amt <= 0:
            errors.append("proposed_repair.amount must be > 0")
        if amt > cat["limit"]:
            errors.append(f"amount {amt} exceeds authority limit {cat['limit']} for {btype} — escalate (out of scope)")
    if not rep.get("target"):
        errors.append("proposed_repair.target is required")
    if cat["action"] == "rebook_trade" and not rep.get("source"):
        errors.append("proposed_repair.source (the incorrect book) is required for rebook_trade")
    if not cat["reversible"]:
        errors.append(f"repair for {btype} is not reversible — out of scope for auto-planning")

    ev = doc.get("evidence") or {}
    missing_ev = [e for e in cat["evidence"] if not ev.get(e)]
    if missing_ev:
        errors.append(f"missing required evidence for {btype}: {', '.join(missing_ev)}")

    if not doc.get("catalog_version"):
        warnings.append("no catalog_version — record the versioned catalog used for reproducibility")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "break_example.json"
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
