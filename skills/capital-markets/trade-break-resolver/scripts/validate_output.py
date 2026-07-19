#!/usr/bin/env python3
"""Deterministic plan/output validation for trade-break-resolver.

Run after planning AND before execution. Enforces the R4 approval-gated guardrails:
  1. Repair is a catalog action within the CATALOG authority limit for the break type;
     the plan cannot self-declare a higher authority than the catalog grants; reversible.
  2. Every step is idempotent, precondition-guarded, verifiable, and reversible.
  3. plan_hash is PRESENT and matches the plan contents (tamper detection). A missing or
     blank hash fails closed — an unhashable plan cannot be trusted for execution.
  4. Pre-execution the plan is BLOCKED and approval is PENDING.
  5. No step is executed without a valid approval token: approval status approved, a token
     is present, an approver is recorded, and the approver's role matches the catalog-required
     approver role for the break type.
  6. Amounts tie to the repair amount; standing note present.

The authority limit and required approver role are read from the SAME permissible-repair
catalog the planning engine uses (validate_input.CATALOG) — never from the plan's own
self-declared fields, which an attacker could inflate.

A REJECTED plan (out-of-catalog/over-limit) passes iff it stays blocked with no execution.

Usage: python validate_output.py plan.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path
from importlib import import_module

sys.path.insert(0, str(Path(__file__).resolve().parent))
CATALOG = import_module("validate_input").CATALOG  # single source of truth (engine reads the same)

# Permissible catalog actions, derived from the catalog so the two never diverge.
CATALOG_ACTIONS = {c["action"] for c in CATALOG.values()}
STEP_FIELDS = ("idempotency_key", "precondition", "expected_effect", "verification", "rollback")
STANDING_NOTE = ("Plan only; no system-of-record change has been executed. "
                 "Execution requires human approval.")


def _recompute_hash(p: dict) -> str:
    core = {"break_id": p.get("break_id"), "trade_id": p.get("trade_id"),
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

    # break type must resolve to a catalog entry (authoritative limit + approver role)
    btype = p.get("break_type")
    cat = CATALOG.get(btype)
    if cat is None:
        errors.append(f"break_type {btype!r} is not in the permissible-repair catalog — out of scope")

    # repair + limit (enforced against the CATALOG limit for the break type, never the
    # plan's own self-declared authority_limit, which could be inflated to bypass the gate)
    if p.get("repair") not in CATALOG_ACTIONS:
        errors.append(f"repair {p.get('repair')!r} is not a permissible catalog action")
    amount = p.get("amount")
    cat_limit = cat["limit"] if cat else None
    if amount is None:
        errors.append("plan missing amount")
    elif cat_limit is not None and amount > cat_limit:
        errors.append(f"amount {amount} exceeds authority limit {cat_limit} for {btype} — out of scope")
    # a plan may not claim a higher authority than the catalog grants for its break type
    declared = p.get("authority_limit")
    if declared is not None and cat_limit is not None and declared > cat_limit:
        errors.append(f"plan self-declares authority_limit {declared} above the catalog limit "
                      f"{cat_limit} for {btype} — tampered or out of scope")
    if not p.get("reversible", False):
        errors.append("repair is not marked reversible")

    # steps
    steps = p.get("steps") or []
    if not steps:
        errors.append("plan has no steps")
    effect_amts = []
    for s in steps:
        for f in STEP_FIELDS:
            if not s.get(f):
                errors.append(f"step {s.get('step_id', '?')}: missing {f}")
        ea = s.get("effect_amount")
        if ea is not None:
            effect_amts.append(ea)
            if amount is not None and ea > amount + 1e-9:
                errors.append(f"step {s.get('step_id', '?')}: effect_amount {ea} exceeds repair amount {amount}")
    if amount is not None and not any(abs((ea or 0) - amount) < 1e-6 for ea in effect_amts):
        errors.append(f"no step effect ties to the repair amount {amount}")

    # tamper detection (fail closed: a missing/blank hash cannot be trusted)
    if not p.get("plan_hash"):
        errors.append("plan_hash is missing or blank — plan integrity cannot be verified (fail closed)")
    elif _recompute_hash(p) != p["plan_hash"]:
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
        # the approver must hold the catalog-mandated approver role for this break type;
        # a plan cannot self-declare a laxer required_role to admit a lower authority.
        required_role = cat["approver"] if cat else appr.get("required_role")
        approver_role = appr.get("approver_role")
        if not approver_role or approver_role != required_role:
            errors.append(f"execution approver role {approver_role!r} does not match required role "
                          f"{required_role!r} — executed by wrong or insufficient authority")
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
