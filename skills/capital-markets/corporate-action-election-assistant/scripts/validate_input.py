#!/usr/bin/env python3
"""Deterministic input validation for corporate-action-election-assistant.

Validates a voluntary corporate-action election request (a confirmed event, the eligible
position, a submission deadline, and a chosen option/legs) BEFORE an election plan is built.
Fails closed on structural problems, a non-permissible option, over-election beyond the
eligible position, notional above the authority limit, an irreversible event, or a request
made past the submission deadline.

This script never submits, records, or confirms an election. It only screens the request.

Input schema (JSON): see references/domain-rules.md. Key fields:
  event_id, account, event_type, catalog_version, reference_price, eligible_quantity,
  as_of, submission_deadline, market_deadline, evidence{...},
  proposed_election{action, legs[{option, quantity}] | option, quantity}

Usage: python validate_input.py election.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from datetime import date
from pathlib import Path

# Permissible-election catalog (default; deployment supplies a versioned catalog).
# Each entry: submittable options, quantity basis, oversubscription cap, reversibility,
# notional authority limit (elected market value), approver role, required evidence.
CATALOG = {
    "tender_offer": {"action": "submit_election", "options": ["tender"], "basis": "up_to",
                     "oversubscribe_cap": 1.0, "reversible": True, "notional_limit": 5000000,
                     "approver": "corporate-actions-supervisor",
                     "evidence": ["offer_notice", "eligible_position", "response_deadline"]},
    "exchange_offer": {"action": "submit_election", "options": ["exchange"], "basis": "up_to",
                       "oversubscribe_cap": 1.0, "reversible": True, "notional_limit": 5000000,
                       "approver": "corporate-actions-supervisor",
                       "evidence": ["offer_notice", "eligible_position", "response_deadline"]},
    "dividend_option": {"action": "submit_election", "options": ["cash", "shares"], "basis": "entire",
                        "oversubscribe_cap": 1.0, "reversible": True, "notional_limit": 1000000,
                        "approver": "corporate-actions-specialist",
                        "evidence": ["event_notice", "eligible_position", "response_deadline"]},
    "rights_subscription": {"action": "submit_election", "options": ["subscribe", "oversubscribe"],
                            "basis": "up_to", "oversubscribe_cap": 2.0, "reversible": True,
                            "notional_limit": 2000000, "approver": "corporate-actions-supervisor",
                            "evidence": ["rights_notice", "eligible_position", "response_deadline"]},
    "conversion": {"action": "submit_election", "options": ["convert"], "basis": "up_to",
                   "oversubscribe_cap": 1.0, "reversible": True, "notional_limit": 2000000,
                   "approver": "corporate-actions-supervisor",
                   "evidence": ["conversion_notice", "eligible_position", "response_deadline"]},
}
OVERSUB_OPTIONS = {"oversubscribe"}
REQUIRED_TOP = ("event_id", "account", "event_type", "eligible_quantity", "reference_price",
                "as_of", "submission_deadline", "proposed_election")
TOL = 1e-6


def legs_of(pe: dict):
    """Normalize proposed_election into a list of {option, quantity} legs.

    Returns (legs, error_message). Supports either an explicit legs[] list or a single
    option+quantity pair. Shared with the plan builder so both read the request identically.
    """
    if not isinstance(pe, dict):
        return [], "proposed_election must be an object"
    raw = pe.get("legs")
    if raw is None:
        if pe.get("option") is None or pe.get("quantity") is None:
            return [], "proposed_election must provide legs[] or option+quantity"
        raw = [{"option": pe.get("option"), "quantity": pe.get("quantity")}]
    if not isinstance(raw, list) or not raw:
        return [], "proposed_election.legs must be a non-empty list"
    legs = []
    for i, leg in enumerate(raw):
        if not isinstance(leg, dict):
            return [], f"leg {i} must be an object"
        legs.append({"option": leg.get("option"), "quantity": leg.get("quantity")})
    return legs, None


def _as_date(v):
    try:
        return date.fromisoformat(str(v))
    except (TypeError, ValueError):
        return None


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    etype = doc["event_type"]
    cat = CATALOG.get(etype)
    if not cat:
        errors.append(f"event type {etype!r} not in permissible-election catalog — escalate (out of scope)")
        return errors, warnings

    pe = doc.get("proposed_election") or {}
    if pe.get("action") != cat["action"]:
        errors.append(f"proposed action {pe.get('action')!r} != catalog action {cat['action']!r} for {etype}")

    legs, leg_err = legs_of(pe)
    if leg_err:
        errors.append(leg_err)
        return errors, warnings

    instructed = 0.0
    for leg in legs:
        opt = leg.get("option")
        if opt not in cat["options"]:
            errors.append(f"option {opt!r} not permissible for {etype} "
                          f"(allowed: {', '.join(cat['options'])})")
        q = leg.get("quantity")
        try:
            q = float(q)
        except (TypeError, ValueError):
            errors.append(f"leg option {opt!r}: quantity is not numeric")
            continue
        if q <= 0:
            errors.append(f"leg option {opt!r}: quantity must be > 0")
        else:
            instructed += q

    try:
        eligible = float(doc["eligible_quantity"])
    except (TypeError, ValueError):
        errors.append("eligible_quantity is not numeric")
        eligible = None
    try:
        price = float(doc["reference_price"])
    except (TypeError, ValueError):
        errors.append("reference_price is not numeric")
        price = None
    if eligible is not None and eligible <= 0:
        errors.append("eligible_quantity must be > 0")
    if price is not None and price <= 0:
        errors.append("reference_price must be > 0")

    # over-election / basis check
    if eligible and eligible > 0:
        cap = cat["oversubscribe_cap"] if any(l.get("option") in OVERSUB_OPTIONS for l in legs) else 1.0
        if cat["basis"] == "entire":
            if abs(instructed - eligible) > TOL:
                errors.append(f"for {etype} the election must allocate the entire eligible position "
                              f"(instructed {instructed} != eligible {eligible})")
        else:  # up_to
            if instructed > eligible * cap + TOL:
                errors.append(f"instructed quantity {instructed} exceeds eligible position {eligible} "
                              f"(cap {cap}) — over-election, out of scope")

    # notional authority limit
    if price is not None and instructed > 0:
        notional = round(instructed * price, 2)
        if notional > cat["notional_limit"]:
            errors.append(f"election notional {notional} exceeds authority limit "
                          f"{cat['notional_limit']} for {etype} — escalate (out of scope)")

    # reversibility (irreversible events are out of scope for auto-planning)
    if not cat["reversible"]:
        errors.append(f"election for {etype} is not reversible before the deadline — out of scope")

    # deadline window: the plan is built strictly before the submission deadline
    a = _as_date(doc.get("as_of"))
    d = _as_date(doc.get("submission_deadline"))
    if a is None:
        errors.append("as_of is not a valid ISO date (YYYY-MM-DD)")
    if d is None:
        errors.append("submission_deadline is not a valid ISO date (YYYY-MM-DD)")
    if a and d and a >= d:
        errors.append(f"as_of {a.isoformat()} is on/after submission deadline {d.isoformat()} — "
                      f"past the election window, fail closed")

    # evidence completeness
    ev = doc.get("evidence") or {}
    missing_ev = [e for e in cat["evidence"] if not ev.get(e)]
    if missing_ev:
        errors.append(f"missing required evidence for {etype}: {', '.join(missing_ev)}")

    if not doc.get("catalog_version"):
        warnings.append("no catalog_version — record the versioned catalog used for reproducibility")
    if not doc.get("interpretation_id"):
        warnings.append("no interpretation_id — link the upstream corporate-action interpretation for lineage")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "election_example.json"
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
