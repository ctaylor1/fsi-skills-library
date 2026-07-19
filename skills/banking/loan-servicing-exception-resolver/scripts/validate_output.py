#!/usr/bin/env python3
"""Deterministic plan/output validation for loan-servicing-exception-resolver.

Run after planning AND before execution. Enforces the R4 approval-gated guardrails:
  1. Remedy is a catalog action within the authority limit; reversible.
  2. Every step is idempotent, precondition-guarded, verifiable, and reversible.
  3. plan_hash is present (mandatory for non-rejected plans) and matches the plan
     contents; a missing/blank hash fails closed (tamper detection).
  4. Pre-execution the plan is BLOCKED and approval is PENDING.
  5. No step is executed without a valid approval token (status approved, approver
     recorded, and approver_role equals the plan's required_role; missing role fails closed).
  6. Amounts tie to the remedy amount; standing note present.

A REJECTED plan (out-of-catalog/over-limit) passes iff it stays blocked with no execution.

Usage: python validate_output.py plan.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

CATALOG_ACTIONS = {"reallocate_payment", "reverse_fee", "adjust_escrow", "refund_duplicate"}
STEP_FIELDS = ("idempotency_key", "precondition", "expected_effect", "verification", "rollback")
STANDING_NOTE = ("Plan only; no system-of-record change has been executed. "
                 "Execution requires human approval.")


def _recompute_hash(p: dict) -> str:
    core = {"exception_id": p.get("exception_id"), "loan_id": p.get("loan_id"),
            "remedy": p.get("remedy"), "amount": p.get("amount"), "target": p.get("target"),
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

    # remedy + limit
    if p.get("remedy") not in CATALOG_ACTIONS:
        errors.append(f"remedy {p.get('remedy')!r} is not a permissible catalog action")
    amount = p.get("amount")
    limit = p.get("authority_limit")
    if amount is None or limit is None:
        errors.append("plan missing amount or authority_limit")
    elif amount > limit:
        errors.append(f"amount {amount} exceeds authority limit {limit} — out of scope")
    if not p.get("reversible", False):
        errors.append("remedy is not marked reversible")

    # steps
    steps = p.get("steps") or []
    if not steps:
        errors.append("plan has no steps")
    effect_amts = []
    for s in steps:
        for f in STEP_FIELDS:
            if not s.get(f):
                errors.append(f"step {s.get('step_id','?')}: missing {f}")
        ea = s.get("effect_amount")
        if ea is not None:
            effect_amts.append(ea)
            if amount is not None and ea > amount + 1e-9:
                errors.append(f"step {s.get('step_id','?')}: effect_amount {ea} exceeds remedy amount {amount}")
    if amount is not None and not any(abs((ea or 0) - amount) < 1e-6 for ea in effect_amts):
        errors.append(f"no step effect ties to the remedy amount {amount}")

    # tamper detection — plan_hash is mandatory for any non-rejected plan; absence fails closed.
    plan_hash = p.get("plan_hash")
    if not plan_hash or not str(plan_hash).strip():
        errors.append("plan_hash missing or blank — cannot verify plan integrity (fail closed)")
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
        # execution claimed -> require a valid approval token + matching approver role
        if appr.get("status") != "approved":
            errors.append("execution present but approval.status is not 'approved' — executed without approval")
        if not appr.get("token"):
            errors.append("execution present but no approval token — executed without a valid token")
        if not appr.get("approver"):
            errors.append("execution present but no approver recorded")
        # Approver-role gate: the approving party must hold the plan's required role.
        # Fail closed if either role is absent — an unverifiable role is not an approval.
        required_role = appr.get("required_role")
        approver_role = appr.get("approver_role")
        if not required_role:
            errors.append("execution present but plan has no required approver role — cannot verify authority (fail closed)")
        if not approver_role:
            errors.append("execution present but approver_role is missing — cannot verify the approver holds the required role (fail closed)")
        elif required_role and approver_role != required_role:
            errors.append(f"approver_role {approver_role!r} does not match required role {required_role!r} — executed by the wrong role")
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
