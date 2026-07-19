#!/usr/bin/env python3
"""Deterministic plan/output validation for corporate-action-election-assistant.

Run after building the election plan AND again before submission. Enforces the R4
approval-gated guardrails and fails closed on any miss:

  1. Election action is a permissible catalog action; every leg option is permissible for
     the event type.
  2. Leg quantities tie to instructed_quantity; instructed quantity does not over-elect the
     eligible position (entire-basis events must allocate the whole position).
  3. Notional does not exceed the authority limit and ties to instructed x reference_price;
     the event is reversible before the deadline.
  4. The request is inside the submission window (as_of strictly before submission_deadline).
  5. Every step is idempotent, precondition-guarded, verifiable, and reversible; step effect
     quantities tie to the instructed quantity.
  6. plan_hash is present and matches the plan contents (tamper detection); a missing or
     blank hash is a hard error — integrity cannot be verified, so the plan fails closed.
  7. Pre-submission the plan is BLOCKED and approval is PENDING with the standing note.
  8. No step is submitted without a valid approval token (status approved, approver, token).

A REJECTED plan (out-of-catalog / over-limit / past-window) passes iff it stays blocked
with no submitted steps and lists reasons.

This is a self-contained authority: it embeds the catalog constraints (defense in depth)
rather than trusting fields the plan asserts about itself.

Usage: python validate_output.py plan.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import hashlib, json, sys
from datetime import date
from pathlib import Path

ELECTION_ACTIONS = {"submit_election"}
STEP_FIELDS = ("idempotency_key", "precondition", "expected_effect", "verification", "rollback")
STANDING_NOTE = ("Plan only; no election has been submitted to the custodian or agent. "
                 "Submission requires human approval.")
OVERSUB_OPTIONS = {"oversubscribe"}
TOL = 1e-6

# Embedded catalog constraints (must match scripts/validate_input.py CATALOG).
CATALOG_CONSTRAINTS = {
    "tender_offer": {"options": {"tender"}, "basis": "up_to", "oversubscribe_cap": 1.0, "notional_limit": 5000000},
    "exchange_offer": {"options": {"exchange"}, "basis": "up_to", "oversubscribe_cap": 1.0, "notional_limit": 5000000},
    "dividend_option": {"options": {"cash", "shares"}, "basis": "entire", "oversubscribe_cap": 1.0, "notional_limit": 1000000},
    "rights_subscription": {"options": {"subscribe", "oversubscribe"}, "basis": "up_to", "oversubscribe_cap": 2.0, "notional_limit": 2000000},
    "conversion": {"options": {"convert"}, "basis": "up_to", "oversubscribe_cap": 1.0, "notional_limit": 2000000},
}


def _recompute_hash(p: dict) -> str:
    core = {
        "event_id": p.get("event_id"), "account": p.get("account"),
        "event_type": p.get("event_type"), "election_action": p.get("election_action"),
        "permissible_options": p.get("permissible_options"), "basis": p.get("basis"),
        "effective_cap": p.get("effective_cap"),
        "instructed_quantity": p.get("instructed_quantity"),
        "eligible_quantity": p.get("eligible_quantity"),
        "reference_price": p.get("reference_price"), "notional": p.get("notional"),
        "authority_limit": p.get("authority_limit"), "reversible": p.get("reversible"),
        "as_of": p.get("as_of"), "submission_deadline": p.get("submission_deadline"),
        "legs": p.get("legs"), "steps": p.get("steps"),
        "expected_post_state": p.get("expected_post_state"),
    }
    return hashlib.sha256(json.dumps(core, sort_keys=True).encode()).hexdigest()


def _as_date(v):
    try:
        return date.fromisoformat(str(v))
    except (TypeError, ValueError):
        return None


def validate(p: dict) -> list[str]:
    errors: list[str] = []
    execu = p.get("execution") or {}
    executed = execu.get("executed_steps") or []

    if p.get("status") == "rejected":
        if execu.get("state") != "blocked" or executed:
            errors.append("rejected plan must remain blocked with no submitted steps")
        if not p.get("reasons"):
            errors.append("rejected plan must list reasons")
        return errors

    # 1. permissible action + event type
    if p.get("election_action") not in ELECTION_ACTIONS:
        errors.append(f"election_action {p.get('election_action')!r} is not a permissible catalog action")
    etype = p.get("event_type")
    cons = CATALOG_CONSTRAINTS.get(etype)
    if not cons:
        errors.append(f"event_type {etype!r} not in permissible-election catalog")

    # 1b. legs permissible
    legs = p.get("legs") or []
    if not legs:
        errors.append("plan has no election legs")
    leg_sum = 0.0
    for leg in legs:
        opt = leg.get("option")
        if cons and opt not in cons["options"]:
            errors.append(f"leg option {opt!r} not permissible for {etype} "
                          f"(allowed: {', '.join(sorted(cons['options']))})")
        try:
            q = float(leg.get("quantity"))
            if q <= 0:
                errors.append(f"leg option {opt!r}: quantity must be > 0")
            leg_sum += q
        except (TypeError, ValueError):
            errors.append(f"leg option {opt!r}: quantity is not numeric")

    # 2. tie-out + over-election
    instructed = p.get("instructed_quantity")
    eligible = p.get("eligible_quantity")
    if instructed is None or eligible is None:
        errors.append("plan missing instructed_quantity or eligible_quantity")
    else:
        if abs(leg_sum - instructed) > 1e-4:
            errors.append(f"leg quantities {leg_sum} do not tie to instructed_quantity {instructed}")
        if cons:
            cap = cons["oversubscribe_cap"] if any(l.get("option") in OVERSUB_OPTIONS for l in legs) else 1.0
            if cons["basis"] == "entire":
                if abs(instructed - eligible) > 1e-4:
                    errors.append(f"instructed quantity {instructed} does not equal eligible position "
                                  f"{eligible} for entire-basis event {etype} — fail closed")
            elif instructed > eligible * cap + 1e-4:
                errors.append(f"instructed quantity {instructed} exceeds eligible position {eligible} "
                              f"(cap {cap}) — over-election, out of scope")

    # 3. notional authority limit + tie + reversibility
    notional = p.get("notional")
    limit = p.get("authority_limit")
    price = p.get("reference_price")
    if notional is None or limit is None:
        errors.append("plan missing notional or authority_limit")
    else:
        if notional > limit + 1e-4:
            errors.append(f"notional {notional} exceeds authority limit {limit} — out of scope")
        if cons and limit != cons["notional_limit"]:
            errors.append(f"authority_limit {limit} does not match catalog limit "
                          f"{cons['notional_limit']} for {etype}")
    if notional is not None and instructed is not None and price is not None:
        if abs(notional - round(instructed * price, 2)) > 1e-2:
            errors.append(f"notional {notional} does not tie to instructed_quantity x reference_price")
    if not p.get("reversible", False):
        errors.append("election is not marked reversible")

    # 4. submission window
    a = _as_date(p.get("as_of"))
    d = _as_date(p.get("submission_deadline"))
    if a is None or d is None:
        errors.append("plan missing valid as_of or submission_deadline")
    elif a >= d:
        errors.append(f"as_of {a.isoformat()} is on/after submission deadline {d.isoformat()} — "
                      f"past the election window, fail closed")

    # 5. steps complete + tie
    steps = p.get("steps") or []
    if not steps:
        errors.append("plan has no steps")
    effect_sum = 0.0
    for s in steps:
        for f in STEP_FIELDS:
            if not s.get(f):
                errors.append(f"step {s.get('step_id', '?')}: missing {f}")
        eq = s.get("effect_quantity")
        if eq is not None:
            effect_sum += eq
            if instructed is not None and eq > instructed + 1e-4:
                errors.append(f"step {s.get('step_id', '?')}: effect_quantity {eq} exceeds instructed {instructed}")
    if instructed is not None and steps and abs(effect_sum - instructed) > 1e-4:
        errors.append(f"step effect quantities {effect_sum} do not tie to instructed_quantity {instructed}")

    # 6. tamper detection — plan_hash MUST be present and match (fail closed).
    # A missing or blank hash is a hard error: without it there is nothing for the approval
    # token to bind to, so a plan whose content was edited and whose plan_hash field was then
    # removed would otherwise slip through unverified (fail-open bypass).
    plan_hash = p.get("plan_hash")
    if not (isinstance(plan_hash, str) and plan_hash.strip()):
        errors.append("plan_hash missing or blank — integrity cannot be verified, fail closed")
    elif _recompute_hash(p) != plan_hash:
        errors.append("plan_hash does not match plan contents (tampered or edited after hashing)")

    # 7/8. approval gate
    appr = p.get("approval") or {}
    if not executed and execu.get("state") != "executed":
        if appr.get("status") != "pending" or execu.get("state") != "blocked":
            errors.append(f"pre-submission plan must be approval=pending & execution=blocked "
                          f"(got approval={appr.get('status')}, execution={execu.get('state')})")
        if STANDING_NOTE.lower() not in str(p.get("standing_note", "")).lower():
            errors.append("missing standing note (pre-submission)")
    else:
        if appr.get("status") != "approved":
            errors.append("execution present but approval.status is not 'approved' — executed without approval")
        if not appr.get("token"):
            errors.append("execution present but no approval token — executed without a valid token")
        if not appr.get("approver"):
            errors.append("execution present but no approver recorded")
    return errors


def main(argv):
    if "--selftest" in argv:
        pth = Path(__file__).resolve().parents[1] / "evals" / "files" / "plan_example.json"
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
