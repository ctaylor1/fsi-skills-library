#!/usr/bin/env python3
"""Deterministic input validation for omnichannel-case-orchestrator.

Validates a confirmed service case + its proposed resolution actions before planning.
Fails closed on structural problems or any action that is not permissible / over its
authority limit / missing required evidence, or a plan whose total monetary exposure
exceeds the plan authority cap.

Input schema (JSON): see references/domain-rules.md. Key fields:
  case_id, customer_id, channels[], catalog_version,
  proposed_actions[]{action_id, type, action, amount, target, evidence{...}}

Usage: python validate_input.py case.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

# Permissible-action catalog (default; deployment supplies a versioned catalog).
# monetary actions carry a positive authority limit; non-monetary actions (account
# changes, outbound commitments) carry limit 0 and must move no money, yet still gate
# on human approval because they change an account or make a customer commitment.
CATALOG = {
    "fee_adjustment": {"action": "waive_fee", "limit": 250, "monetary": True, "reversible": True,
                       "approver": "case-supervisor", "evidence": ["fee_record", "eligibility"]},
    "goodwill_credit": {"action": "issue_goodwill_credit", "limit": 100, "monetary": True, "reversible": True,
                        "approver": "case-supervisor", "evidence": ["goodwill_matrix_ref", "reason_code"]},
    "billing_refund": {"action": "refund_overcharge", "limit": 500, "monetary": True, "reversible": True,
                       "approver": "case-supervisor", "evidence": ["billing_record", "overcharge_evidence"]},
    "account_change": {"action": "update_contact_preference", "limit": 0, "monetary": False, "reversible": True,
                       "approver": "account-specialist", "evidence": ["verified_identity", "customer_request"]},
    "outbound_commitment": {"action": "send_resolution_confirmation", "limit": 0, "monetary": False, "reversible": True,
                            "approver": "qa-reviewer", "evidence": ["approved_template_id", "customer_consent"]},
}
# Aggregate monetary exposure across all actions in one plan may not exceed this cap.
PLAN_AUTHORITY_CAP = 1000
# Approver seniority; the plan requires the most senior role across its actions.
ROLE_RANK = {"case-agent": 1, "qa-reviewer": 2, "account-specialist": 2, "case-supervisor": 3}
REQUIRED_TOP = ("case_id", "customer_id", "channels", "proposed_actions")


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not isinstance(doc.get("channels"), list) or not doc["channels"]:
        errors.append("channels must be a non-empty list (the channels this case touched)")
    actions = doc.get("proposed_actions")
    if not isinstance(actions, list) or not actions:
        errors.append("proposed_actions must be a non-empty list")
        return errors, warnings

    total_exposure = 0.0
    seen_ids = set()
    for a in actions:
        aid = a.get("action_id") or "?"
        if aid in seen_ids:
            errors.append(f"action {aid}: duplicate action_id (idempotency keys must be unique)")
        seen_ids.add(aid)

        atype = a.get("type")
        cat = CATALOG.get(atype)
        if not cat:
            errors.append(f"action {aid}: type {atype!r} not in permissible-action catalog — escalate (out of scope)")
            continue
        if a.get("action") != cat["action"]:
            errors.append(f"action {aid}: action {a.get('action')!r} != catalog action {cat['action']!r} for {atype}")

        amt = _num(a.get("amount"))
        if amt is None:
            errors.append(f"action {aid}: amount is not numeric")
        elif amt < 0:
            errors.append(f"action {aid}: amount must be >= 0")
        elif cat["monetary"]:
            if amt <= 0:
                errors.append(f"action {aid}: monetary action must have amount > 0")
            if amt > cat["limit"]:
                errors.append(f"action {aid}: amount {amt} exceeds authority limit {cat['limit']} for {atype} — escalate (out of scope)")
            total_exposure += amt
        else:
            if amt != 0:
                errors.append(f"action {aid}: non-monetary {atype} must have amount 0 (no money may move)")

        if not a.get("target"):
            errors.append(f"action {aid}: target is required")
        if not cat["reversible"]:
            errors.append(f"action {aid}: {atype} is not reversible — out of scope for auto-planning")

        ev = a.get("evidence") or {}
        missing_ev = [e for e in cat["evidence"] if not ev.get(e)]
        if missing_ev:
            errors.append(f"action {aid}: missing required evidence for {atype}: {', '.join(missing_ev)}")

    if total_exposure > PLAN_AUTHORITY_CAP:
        errors.append(f"total monetary exposure {round(total_exposure, 2)} exceeds plan authority cap {PLAN_AUTHORITY_CAP} — escalate (out of scope)")

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
