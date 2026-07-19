#!/usr/bin/env python3
"""Deterministic plan/output validation for employee-trading-preclearance-assistant.

Run after planning AND before execution. Enforces the R4 approval-gated guardrails for an
employee personal-trade preclearance decision plan:

  1. Permissible action within limits — decision is one of {approve, approve_with_conditions,
     deny}; an approve* decision is IMPERMISSIBLE when any hard block is present (restricted
     list, active blackout, minimum-holding breach, conflict/MNPI) — fail closed. Notional is
     within the approver's authority limit and the required approver role matches the decision.
  2. Every step is idempotent, precondition-guarded, verifiable, and reversible.
  3. plan_hash is present (mandatory for non-rejected plans) and matches the plan contents;
     a missing/blank hash fails closed (tamper detection).
  4. Pre-execution the plan is BLOCKED and approval is PENDING; standing note present.
  5. No step is executed without a VALID approval token (status approved, token present,
     approver recorded, approver_role equals required_role, and approver != requesting
     employee — SoD); a missing role fails closed.
  6. Decision ties out: a step records the plan decision; an approve* plan clears the exact
     notional; a deny plan issues NO clearance.

A REJECTED plan (over the senior limit / failed input) passes iff it stays blocked with no
execution and lists reasons.

Usage: python validate_output.py plan.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

DECISIONS = {"approve", "approve_with_conditions", "deny"}
APPROVE_SET = {"approve", "approve_with_conditions"}
# decision -> (required approver role, notional authority limit)
EXPECTED = {
    "approve": ("compliance-preclearance-analyst", 100000),
    "approve_with_conditions": ("compliance-officer", 1000000),
    "deny": ("compliance-officer", None),
}
STEP_FIELDS = ("idempotency_key", "precondition", "expected_effect", "verification", "rollback")
STANDING_NOTE = ("Decision plan only; no preclearance decision has been recorded and no "
                 "clearance has been issued. Execution requires compliance approval.")


def _recompute_hash(p: dict) -> str:
    core = {"request_id": p.get("request_id"), "employee_id": p.get("employee_id"),
            "instrument": p.get("instrument"), "side": p.get("side"),
            "quantity": p.get("quantity"),
            "notional_usd": float(p["notional_usd"]) if p.get("notional_usd") is not None else None,
            "decision": p.get("decision"), "conditions": p.get("conditions"),
            "steps": p.get("steps"), "expected_post_state": p.get("expected_post_state")}
    return hashlib.sha256(json.dumps(core, sort_keys=True).encode()).hexdigest()


def _decision_recorded(steps, decision):
    for s in steps:
        for k, v in (s.get("post_state") or {}).items():
            if k.endswith(":decision") and v == decision:
                return True
    return False


def _clearance_issued(steps):
    for s in steps:
        if s.get("cleared_notional") is not None:
            return True
        for k, v in (s.get("post_state") or {}).items():
            if k.endswith(":clearance_state") and v == "cleared":
                return True
    return False


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

    decision = p.get("decision")
    hard_blocks = p.get("hard_blocks") or []

    # 1. permissible action within limits
    if decision not in DECISIONS:
        errors.append(f"decision {decision!r} is not a permissible preclearance decision")
    else:
        exp_role, exp_limit = EXPECTED[decision]
        if decision in APPROVE_SET and hard_blocks:
            errors.append(f"decision {decision!r} impermissible: hard block(s) present "
                          f"{hard_blocks} — fail closed (only 'deny' is permissible)")
        appr = p.get("approval") or {}
        if appr.get("required_role") != exp_role:
            errors.append(f"required approver role {appr.get('required_role')!r} != expected "
                          f"{exp_role!r} for decision {decision!r}")
        if decision in APPROVE_SET:
            notional = p.get("notional_usd")
            limit = p.get("authority_limit")
            if notional is None or limit is None:
                errors.append("plan missing notional_usd or authority_limit")
            elif notional > limit:
                errors.append(f"notional {notional} exceeds authority limit {limit} — out of scope")
            if limit != exp_limit:
                errors.append(f"authority_limit {limit} != expected {exp_limit} for {decision!r}")

    # 2. steps complete, idempotent, verifiable, reversible
    steps = p.get("steps") or []
    if not steps:
        errors.append("plan has no steps")
    for s in steps:
        sid = s.get("step_id", "?")
        for f in STEP_FIELDS:
            if not s.get(f):
                errors.append(f"step {sid}: missing {f}")
        if not (s.get("post_state") or {}):
            errors.append(f"step {sid}: missing post_state")

    # 3. tamper detection — plan_hash is mandatory for any non-rejected plan; absence fails closed.
    plan_hash = p.get("plan_hash")
    if not plan_hash or not str(plan_hash).strip():
        errors.append("plan_hash missing or blank — cannot verify plan integrity (fail closed)")
    elif _recompute_hash(p) != plan_hash:
        errors.append("plan_hash does not match plan contents (tampered or edited after hashing)")

    # 6. decision tie-out / clearance consistency
    if decision in DECISIONS:
        if not _decision_recorded(steps, decision):
            errors.append(f"no step records the plan decision {decision!r}")
        cleared = _clearance_issued(steps)
        if decision in APPROVE_SET:
            notional = p.get("notional_usd")
            tie = any(s.get("cleared_notional") is not None
                      and abs(float(s["cleared_notional"]) - float(notional)) < 1e-6
                      for s in steps) if notional is not None else False
            if not tie:
                errors.append(f"no clearance step ties to the plan notional {p.get('notional_usd')}")
            if not cleared:
                errors.append("approve decision but no step issues a clearance")
        elif decision == "deny" and cleared:
            errors.append("deny decision must NOT issue a clearance — fail closed")

    # 4/5. approval gate
    appr = p.get("approval") or {}
    if not executed and execu.get("state") != "executed":
        if appr.get("status") != "pending" or execu.get("state") != "blocked":
            errors.append(f"pre-execution plan must be approval=pending & execution=blocked "
                          f"(got approval={appr.get('status')}, execution={execu.get('state')})")
        if STANDING_NOTE.lower() not in str(p.get("standing_note", "")).lower():
            errors.append("missing standing note (pre-execution)")
    else:
        if appr.get("status") != "approved":
            errors.append("execution present but approval.status is not 'approved' — executed without approval")
        if not appr.get("token"):
            errors.append("execution present but no approval token — executed without a valid token")
        if not appr.get("approver"):
            errors.append("execution present but no approver recorded")
        elif p.get("employee_id") and appr.get("approver") == p.get("employee_id"):
            errors.append("approver equals the requesting employee — segregation-of-duties violation")
        # Approver must hold the plan's required role; a missing/mismatched role fails closed.
        required_role = appr.get("required_role")
        approver_role = appr.get("approver_role")
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
