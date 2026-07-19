#!/usr/bin/env python3
"""Deterministic plan/output validation for payment-repair-assistant.

Run after planning AND before execution. Enforces the R4 approval-gated guardrails:
  1. Repair is a catalog action within the authority limit; reversible.
  2. Every step is idempotent, precondition-guarded, verifiable, and reversible.
  3. Sanctions screening is cleared for any resubmission/release (compliance gate).
  4. A payment-movement step (resubmit/return) is bound to the payment's end-to-end id
     (duplicate-payment guard).
  5. plan_hash is present, non-empty, and matches the plan contents (tamper detection;
     a non-rejected plan with a missing/blank hash fails closed).
  6. Pre-execution the plan is BLOCKED and approval is PENDING; standing note present.
  7. No step is executed without a valid approval token (status approved, token, approver).
  8. Amounts tie to the repair amount.

A REJECTED plan (out-of-catalog/over-limit/uncleared screening) passes iff it stays blocked
with no execution and lists reasons.

Usage: python validate_output.py plan.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

CATALOG_ACTIONS = {"repair_and_resubmit", "release_and_resubmit", "return_to_originator"}
MOVEMENT_ACTIONS = {"resubmit_payment", "return_payment"}
CLEARED_SCREENING = ("clear", "false_positive_cleared")
STEP_FIELDS = ("idempotency_key", "precondition", "expected_effect", "verification", "rollback")
STANDING_NOTE = ("Plan only; no payment has been resubmitted, released, returned, or "
                 "cancelled. Execution requires human approval.")


def _recompute_hash(p: dict) -> str:
    core = {"case_id": p.get("case_id"), "payment_id": p.get("payment_id"),
            "repair": p.get("repair"), "amount": p.get("amount"), "target": p.get("target"),
            "steps": p.get("steps"), "expected_post_state": p.get("expected_post_state")}
    return hashlib.sha256(json.dumps(core, sort_keys=True).encode()).hexdigest()


def validate(p: dict) -> list[str]:
    errors: list[str] = []
    execu = p.get("execution") or {}
    executed = execu.get("executed_steps") or []

    if p.get("status") == "rejected":
        if execu.get("state") != "blocked" or executed:
            errors.append("rejected plan must remain blocked with no executed steps")
        if not p.get("reasons"):
            errors.append("rejected plan must list reasons")
        return errors

    # repair + limit + reversibility
    if p.get("repair") not in CATALOG_ACTIONS:
        errors.append(f"repair {p.get('repair')!r} is not a permissible catalog action")
    amount = p.get("amount")
    limit = p.get("authority_limit")
    if amount is None or limit is None:
        errors.append("plan missing amount or authority_limit")
    elif amount > limit:
        errors.append(f"amount {amount} exceeds authority limit {limit} — out of scope")
    if not p.get("reversible", False):
        errors.append("repair is not marked reversible")

    # compliance gate: resubmission/release requires cleared sanctions screening
    if p.get("screening_required", False):
        status = (p.get("screening") or {}).get("status")
        if status not in CLEARED_SCREENING:
            errors.append(f"sanctions screening not cleared (status={status!r}) — "
                          f"resubmission blocked; route to sanctions/compliance")

    # steps
    steps = p.get("steps") or []
    if not steps:
        errors.append("plan has no steps")
    effect_amts = []
    for s in steps:
        for f in STEP_FIELDS:
            if not s.get(f):
                errors.append(f"step {s.get('step_id', '?')}: missing {f}")
        # duplicate-payment guard: a movement step must be bound to the end-to-end id
        if s.get("action") in MOVEMENT_ACTIONS and not s.get("end_to_end_id"):
            errors.append(f"step {s.get('step_id', '?')}: movement step missing end_to_end_id "
                          f"binding (duplicate-payment guard)")
        ea = s.get("effect_amount")
        if ea is not None:
            effect_amts.append(ea)
            if amount is not None and ea > amount + 1e-9:
                errors.append(f"step {s.get('step_id', '?')}: effect_amount {ea} exceeds repair amount {amount}")
    if amount is not None and not any(abs((ea or 0) - amount) < 1e-6 for ea in effect_amts):
        errors.append(f"no step effect ties to the repair amount {amount}")

    # tamper detection (fail closed): a non-rejected plan MUST carry a non-empty
    # plan_hash that matches the recomputed hash. Omitting or blanking plan_hash must
    # NOT skip the check — otherwise content could be tampered and the hash dropped to
    # evade detection (the approval token binds to the plan hash).
    plan_hash = p.get("plan_hash")
    if not (isinstance(plan_hash, str) and plan_hash.strip()):
        errors.append("plan_hash missing or empty — a non-rejected plan must carry a "
                      "plan_hash for tamper detection (fail closed)")
    elif _recompute_hash(p) != plan_hash:
        errors.append("plan_hash does not match plan contents (tampered or edited after hashing)")

    # approval gate
    appr = p.get("approval") or {}
    if not executed and execu.get("state") != "executed":
        # pre-execution posture
        if appr.get("status") != "pending" or execu.get("state") != "blocked":
            errors.append(f"pre-execution plan must be approval=pending & execution=blocked "
                          f"(got approval={appr.get('status')}, execution={execu.get('state')})")
        if STANDING_NOTE.lower() not in str(p.get("standing_note", "")).lower():
            errors.append("missing standing note (pre-execution)")
    else:
        # execution claimed -> require a valid approval token + matching role
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
