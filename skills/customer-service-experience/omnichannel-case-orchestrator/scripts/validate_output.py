#!/usr/bin/env python3
"""Deterministic plan/output validation for omnichannel-case-orchestrator.

Run after planning AND before execution. Enforces the R4 approval-gated guardrails:
  1. Every action is a permissible catalog action within its authority limit and reversible.
  2. Total monetary exposure is within the plan authority cap.
  3. Every step is idempotent, precondition-guarded, verifiable, and reversible.
  4. plan_hash is PRESENT and matches the plan contents — a missing/blank hash fails closed
     (tamper detection; required_role is part of the hashed core so it cannot be downgraded
     without breaking the hash).
  5. Pre-execution the plan is BLOCKED and approval is PENDING.
  6. No step is executed without a valid approval token BOUND to the plan hash
     (approval.plan_hash must equal the recomputed hash) AND whose approver holds the
     required role. The required role is RECOMPUTED from the actions' catalog approvers
     (most senior by ROLE_RANK) — never trusted from the stored field — so a downgraded
     required_role cannot lower the approver tier. A plan that claims execution without a
     valid, bound, correctly-authorized approval MUST fail closed.
  7. Each monetary action's amount ties to a plan step's effect; standing note present.

A REJECTED plan (out-of-catalog / over-limit / over-cap) passes iff it stays blocked with
no execution and lists reasons.

Usage: python validate_output.py plan.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

from importlib import import_module
sys.path.insert(0, str(Path(__file__).resolve().parent))
_vi = import_module("validate_input")
# Single source of truth: the same catalog / role ranking the builder and input
# validator use. Reading it here (instead of hardcoding) keeps the validator from
# diverging from the engine's config and lets it recompute the required approver role.
CATALOG = _vi.CATALOG
ROLE_RANK = _vi.ROLE_RANK
CATALOG_ACTIONS = {c["action"] for c in CATALOG.values()}
STEP_FIELDS = ("idempotency_key", "precondition", "expected_effect", "verification", "rollback")
STANDING_NOTE = ("Plan only; no system-of-record change has been executed. "
                 "Execution requires human approval.")


def _recompute_hash(p: dict) -> str:
    # required_role is part of the hashed core so the approver tier cannot be
    # downgraded without breaking tamper detection.
    core = {"case_id": p.get("case_id"), "customer_id": p.get("customer_id"),
            "actions": p.get("actions"), "steps": p.get("steps"),
            "expected_post_state": p.get("expected_post_state"),
            "plan_authority_cap": p.get("plan_authority_cap"),
            "required_role": p.get("required_role")}
    return hashlib.sha256(json.dumps(core, sort_keys=True).encode()).hexdigest()


def _required_role(actions: list) -> str | None:
    """Recompute the required approver role from the actions' catalog approvers.

    The most senior approver (by ROLE_RANK) across all actions is required. Derived from
    the catalog — NOT read from the plan's stored ``required_role`` — so a tampered/downgraded
    required_role cannot lower the authority needed to approve execution.
    """
    max_rank, role = 0, None
    for a in actions or []:
        cat = CATALOG.get(a.get("type"))
        if not cat:
            continue
        rank = ROLE_RANK.get(cat["approver"], 0)
        if rank > max_rank:
            max_rank, role = rank, cat["approver"]
    return role


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

    # actions + per-action limit + reversibility
    actions = p.get("actions") or []
    if not actions:
        errors.append("plan has no actions")
    monetary_amounts, total_exposure = [], 0.0
    for a in actions:
        aid = a.get("action_id", "?")
        if a.get("action") not in CATALOG_ACTIONS:
            errors.append(f"action {aid}: {a.get('action')!r} is not a permissible catalog action")
        amount = a.get("amount")
        limit = a.get("authority_limit")
        if amount is None or limit is None:
            errors.append(f"action {aid}: missing amount or authority_limit")
        elif amount > limit:
            errors.append(f"action {aid}: amount {amount} exceeds authority limit {limit} — out of scope")
        if not a.get("reversible", False):
            errors.append(f"action {aid}: action is not marked reversible")
        if a.get("monetary") and isinstance(amount, (int, float)) and amount > 0:
            monetary_amounts.append(amount)
            total_exposure += amount

    cap = p.get("plan_authority_cap")
    if cap is not None and total_exposure > cap:
        errors.append(f"total monetary exposure {round(total_exposure, 2)} exceeds plan authority cap {cap} — out of scope")

    # steps: idempotent + precondition + verifiable + reversible
    steps = p.get("steps") or []
    if not steps:
        errors.append("plan has no steps")
    step_effects = []
    for s in steps:
        for f in STEP_FIELDS:
            if not s.get(f):
                errors.append(f"step {s.get('step_id', '?')}: missing {f}")
        ea = s.get("effect_amount")
        if isinstance(ea, (int, float)) and ea > 0:
            step_effects.append(ea)

    # tie-out: every monetary action amount must be realized by a plan step effect
    for ma in monetary_amounts:
        if not any(abs(se - ma) < 1e-6 for se in step_effects):
            errors.append(f"no step effect ties to action amount {ma}")

    # tamper detection — plan_hash is MANDATORY on any non-rejected plan and must match.
    # A missing/blank hash means the plan is unverifiable, so fail closed (do not skip).
    recomputed_hash = _recompute_hash(p)
    plan_hash = p.get("plan_hash")
    if not plan_hash:
        errors.append("plan_hash is missing/blank — plan integrity cannot be verified (fail closed)")
    elif recomputed_hash != plan_hash:
        errors.append("plan_hash does not match plan contents (tampered or edited after hashing)")

    # approval gate
    appr = p.get("approval") or {}
    # Required approver role is recomputed from the catalog, never trusted from the field.
    req_role = _required_role(actions)
    if req_role and p.get("required_role") not in (None, req_role):
        errors.append(f"stored required_role {p.get('required_role')!r} does not match the "
                      f"catalog-derived required role {req_role!r} — approver-tier downgrade")
    if not executed and execu.get("state") != "executed":
        # pre-execution posture
        if appr.get("status") != "pending" or execu.get("state") != "blocked":
            errors.append(f"pre-execution plan must be approval=pending & execution=blocked "
                          f"(got approval={appr.get('status')}, execution={execu.get('state')})")
        if STANDING_NOTE.lower() not in str(p.get("standing_note", "")).lower():
            errors.append("missing standing note (pre-execution)")
    else:
        # execution claimed -> require a valid approval token BOUND to the plan hash,
        # with an approver holding the catalog-derived required role. Fail closed otherwise.
        if appr.get("status") != "approved":
            errors.append("execution present but approval.status is not 'approved' — executed without approval")
        if not appr.get("token"):
            errors.append("execution present but no approval token — executed without a valid token")
        if not appr.get("approver"):
            errors.append("execution present but no approver recorded")
        # Token must be bound to THIS plan's hash: a replayed token (approved for a
        # different plan) or an unbound token is invalid.
        approved_hash = appr.get("plan_hash")
        if not approved_hash:
            errors.append("approval token is not bound to any plan hash — unbound token, fail closed")
        elif approved_hash != recomputed_hash:
            errors.append("approval token is bound to a different plan hash (replayed/stale token) — fail closed")
        # Approver must hold the recomputed required role — not the possibly-downgraded field.
        if req_role and appr.get("approver_role") != req_role:
            errors.append(f"approver role {appr.get('approver_role')!r} does not match required role {req_role!r}")
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
