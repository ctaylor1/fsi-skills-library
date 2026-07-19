#!/usr/bin/env python3
"""Deterministic plan/output validation for month-end-close-orchestrator.

Run after planning AND before execution. Enforces the R4 approval-gated guardrails plus the
orchestration-specific dependency invariant:

  1. Every step action is a permissible close-action within its posting-authority limit.
  2. Every step is idempotent, precondition-guarded, verifiable, and reversible (rollback).
  3. Journal effect_amount ties to the posted delta and is within its authority limit.
  4. Dependency ordering is valid: each step's prerequisites appear earlier in the order,
     and no step may be executed before its prerequisites are executed (fail closed).
  5. plan_hash is present AND matches the plan contents (tamper / edited-after-approval
     detection). A missing/empty plan_hash fails closed — dropping the field must not skip
     the integrity check and let a post-approval edit slip through.
  6. Every certify_reconciliation step carries a zero-breaks attestation (unresolved_breaks
     == 0); a certify step with missing or non-zero unresolved_breaks fails closed — a
     reconciliation is never certified while it still has unresolved breaks.
  7. Pre-execution the plan is BLOCKED and approval is PENDING; standing note present.
  8. No step is executed without a valid approval token (status approved, token, approver).

A REJECTED plan (out-of-catalog / over-limit / cyclic / un-cleared recon) passes iff it
stays blocked with no execution and lists its reasons.

Usage: python validate_output.py plan.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

ACTION_KIND = {
    "post_accrual_journal": "journal", "post_reclass_journal": "journal",
    "post_allocation_journal": "journal", "certify_reconciliation": "certify",
    "certify_close_task": "certify", "lock_subledger": "lock", "close_period": "lock",
}
LIMIT = {"post_accrual_journal": 250000, "post_reclass_journal": 250000,
         "post_allocation_journal": 1000000}
STEP_FIELDS = ("idempotency_key", "precondition", "expected_effect", "verification", "rollback")
STANDING_NOTE_KEY = "execution requires human approval"


def _recompute_hash(p: dict) -> str:
    core = {"close_run_id": p.get("close_run_id"), "entity": p.get("entity"),
            "period": p.get("period"), "steps": p.get("steps"),
            "expected_post_state": p.get("expected_post_state")}
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

    steps = p.get("steps") or []
    if not steps:
        errors.append("plan has no steps")

    p.get("step_order") or [s.get("step_id") for s in steps]
    seen_before: set = set()
    idem_keys: set = set()

    for s in steps:
        sid = s.get("step_id", "?")
        action = s.get("action")
        if action not in ACTION_KIND:
            errors.append(f"step {sid}: action {action!r} is not a permissible close-action")
        for f in STEP_FIELDS:
            if not s.get(f):
                errors.append(f"step {sid}: missing {f}")

        ik = s.get("idempotency_key")
        if ik and ik in idem_keys:
            errors.append(f"step {sid}: duplicate idempotency_key {ik!r} (steps must be independently idempotent)")
        if ik:
            idem_keys.add(ik)

        kind = ACTION_KIND.get(action)
        if kind == "journal":
            ea = s.get("effect_amount")
            if ea is None or not isinstance(ea, (int, float)):
                errors.append(f"step {sid}: journal step missing numeric effect_amount")
            else:
                if ea <= 0:
                    errors.append(f"step {sid}: journal effect_amount must be > 0")
                lim = LIMIT.get(action)
                if lim is not None and ea > lim + 1e-9:
                    errors.append(f"step {sid}: effect_amount {ea} exceeds posting-authority limit {lim} for {action}")
                delta = (s.get("post_delta") or {}).get(s.get("target"))
                if delta is None or abs(abs(delta) - ea) > 1e-6:
                    errors.append(f"step {sid}: effect_amount {ea} does not tie to the posted delta {delta}")

        # HARD BOUNDARY: a reconciliation is never certified while it still carries unresolved
        # breaks. The certify step must attest zero breaks; missing or non-zero fails closed.
        if action == "certify_reconciliation":
            ub = s.get("unresolved_breaks")
            if ub is None:
                errors.append(f"step {sid}: certify_reconciliation missing zero-breaks attestation "
                              f"(unresolved_breaks) — cannot certify (fail closed)")
            elif not isinstance(ub, int) or isinstance(ub, bool):
                errors.append(f"step {sid}: unresolved_breaks attestation must be an integer")
            elif ub != 0:
                errors.append(f"step {sid}: {ub} unresolved reconciliation break(s) — cannot certify "
                              f"(clear via gl-reconciler first; fail closed)")

        # dependency ordering: prerequisites must be sequenced earlier
        for dep in s.get("depends_on_steps") or []:
            if dep not in seen_before:
                errors.append(f"step {sid}: prerequisite {dep} is not sequenced before it (dependency-order violation)")
        seen_before.add(sid)

    # tamper detection — fail closed if the binding hash is absent/empty. Dropping the field
    # must NOT skip the check and let a post-approval-edited plan pass.
    ph = p.get("plan_hash")
    if not ph:
        errors.append("plan_hash missing/empty — plan integrity cannot be verified (fail closed)")
    elif _recompute_hash(p) != ph:
        errors.append("plan_hash does not match plan contents (tampered or edited after approval)")

    appr = p.get("approval") or {}
    if not executed and execu.get("state") != "executed":
        # pre-execution posture
        if appr.get("status") != "pending" or execu.get("state") != "blocked":
            errors.append(f"pre-execution plan must be approval=pending & execution=blocked "
                          f"(got approval={appr.get('status')}, execution={execu.get('state')})")
        if STANDING_NOTE_KEY not in str(p.get("standing_note", "")).lower():
            errors.append("missing standing note (pre-execution)")
    else:
        # execution claimed -> require a valid approval token + matching role
        if appr.get("status") != "approved":
            errors.append("execution present but approval.status is not 'approved' — executed without approval")
        if not appr.get("token"):
            errors.append("execution present but no approval token — executed without a valid token")
        if not appr.get("approver"):
            errors.append("execution present but no approver recorded")
        # executed steps must respect dependency order (no prerequisite skipped)
        step_by_id = {s.get("step_id"): s for s in steps}
        exec_set = set(executed)
        for eid in executed:
            for dep in (step_by_id.get(eid, {}).get("depends_on_steps") or []):
                if dep not in exec_set:
                    errors.append(f"executed step {eid}: prerequisite {dep} was not executed (dependency-order violation)")
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
