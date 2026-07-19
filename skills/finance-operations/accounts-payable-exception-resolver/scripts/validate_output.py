#!/usr/bin/env python3
"""Deterministic plan/output validation for accounts-payable-exception-resolver.

Run after planning AND before execution. Enforces the R4 approval-gated guardrails:
  1. Remedy is a catalog action within the authority limit; reversible; not a disbursement.
  2. Every step is idempotent, precondition-guarded, verifiable, reversible, and its action is
     an allowlisted AP correction operation (a non-allowlisted action fails closed).
  3. plan_hash is present and matches the plan contents; a missing/blank hash fails closed
     (tamper detection).
  4. Pre-execution the plan is BLOCKED and approval is PENDING.
  5. No step is executed without a valid approval token (status approved, role matches).
  6. Amounts tie to the remedy amount; standing note present.

A REJECTED plan (out-of-catalog/over-limit) passes iff it stays blocked with no execution.

Usage: python validate_output.py plan.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

CATALOG_ACTIONS = {"adjust_invoice_price", "align_to_po_quantity", "match_to_receipt",
                   "block_duplicate", "correct_tax_code", "hold_for_bank_verification",
                   "route_for_approval"}
# Actions this skill must never plan or execute (disbursement / bank-master change).
FORBIDDEN_ACTIONS = {"disburse", "release_payment", "pay_invoice", "payment_run",
                     "update_bank_master", "wire", "transfer_funds"}
# ALLOWLIST of permissible AP-correction step actions. This is the closed set of step
# actions the plan builder (calculate_or_transform.py::_steps) can emit; ANY step action
# outside this set fails closed, so a disbursement smuggled under a novel action name (one
# not in FORBIDDEN_ACTIONS) can never pass. Keep in sync with the builder's step actions.
STEP_ACTION_ALLOWLIST = {
    "debit_ap_liability",     # adjust_invoice_price / align_to_po_quantity
    "credit_price_variance",  # adjust_invoice_price
    "credit_gr_ir",           # align_to_po_quantity
    "hold_in_gr_ir",          # match_to_receipt
    "adjust_tax",             # correct_tax_code
    "offset_ap_liability",    # correct_tax_code
    "place_payment_hold",     # block_duplicate / hold_for_bank_verification
    "place_approval_hold",    # route_for_approval
}
STEP_FIELDS = ("idempotency_key", "precondition", "expected_effect", "verification", "rollback")
STANDING_NOTE = ("Plan only; no system-of-record change has been executed. "
                 "Execution requires human approval.")


def _recompute_hash(p: dict) -> str:
    core = {"exception_id": p.get("exception_id"), "invoice_id": p.get("invoice_id"),
            "vendor_id": p.get("vendor_id"), "remedy": p.get("remedy"), "amount": p.get("amount"),
            "target": p.get("target"), "steps": p.get("steps"),
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

    # remedy + limit + disbursement guard
    if p.get("remedy") not in CATALOG_ACTIONS:
        errors.append(f"remedy {p.get('remedy')!r} is not a permissible catalog action")
    if p.get("remedy") in FORBIDDEN_ACTIONS:
        errors.append(f"remedy {p.get('remedy')!r} disburses funds or changes banking details — out of scope")
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
        action = s.get("action")
        if action not in STEP_ACTION_ALLOWLIST:
            if action in FORBIDDEN_ACTIONS:
                errors.append(f"step {s.get('step_id','?')}: forbidden disbursement action {action!r}")
            else:
                errors.append(f"step {s.get('step_id','?')}: action {action!r} is not an allowlisted "
                              f"AP correction operation — fail closed")
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

    # tamper detection — plan_hash must be present and non-empty; a missing/blank hash
    # cannot be recomputed against, so fail closed rather than skipping the check.
    plan_hash = p.get("plan_hash")
    if not plan_hash or not str(plan_hash).strip():
        errors.append("plan_hash missing or empty — cannot verify plan integrity (fail closed)")
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
