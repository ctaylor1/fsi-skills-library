#!/usr/bin/env python3
"""Deterministic correction-plan builder for loan-servicing-exception-resolver.

Builds a validated, idempotent correction plan from a confirmed exception + permissible
remedy. The plan is created BLOCKED and PENDING approval; this script never executes,
posts, or changes a system of record. Execution is a separate, approval-gated operation.

Usage: python calculate_or_transform.py exception.json | --selftest
Prints the plan JSON to stdout. A remedy outside the catalog/limit yields a REJECTED plan.
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

from importlib import import_module
sys.path.insert(0, str(Path(__file__).resolve().parent))
CATALOG = import_module("validate_input").CATALOG  # single source of truth
_validate = import_module("validate_input").validate

STANDING_NOTE = ("Plan only; no system-of-record change has been executed. "
                 "Execution requires human approval.")


def _idem(plan_id, step_id, action, amount, target):
    raw = f"{plan_id}|{step_id}|{action}|{amount}|{target}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _steps(plan_id, etype, action, amount, target, source):
    """Return ordered, idempotent, reversible steps + expected post-state deltas."""
    def step(sid, act, pre, effect, effect_amt, verify, rollback, acct, delta):
        return {"step_id": sid, "action": act,
                "idempotency_key": _idem(plan_id, sid, act, effect_amt, acct),
                "precondition": pre, "expected_effect": effect, "effect_amount": effect_amt,
                "verification": verify, "rollback": rollback,
                "post_delta": {acct: delta}}

    if action == "reallocate_payment":
        s1 = step("S1", "debit_source", f"payment of {amount} is held in {source}",
                  f"remove {amount} from {source}", amount,
                  f"{source} balance decreased by {amount}",
                  f"re-credit {amount} to {source}", source, -amount)
        s2 = step("S2", "credit_target", f"loan bucket {target} is open",
                  f"apply {amount} to {target}", amount,
                  f"{target} balance increased by {amount}",
                  f"reverse the {amount} credit to {target}", target, +amount)
        return [s1, s2]
    if action == "reverse_fee":
        return [step("S1", "reverse_fee", f"fee of {amount} is currently assessed on {target}",
                     f"reverse fee {amount} on {target}", amount,
                     f"fee balance on {target} reduced by {amount}",
                     f"re-assess the {amount} fee on {target}", target, -amount)]
    if action == "adjust_escrow":
        return [step("S1", "adjust_escrow", f"escrow account {target} exists",
                     f"adjust escrow {target} by {amount}", amount,
                     f"escrow {target} equals recomputed value (delta {amount})",
                     f"restore escrow {target} to prior balance", target, amount)]
    if action == "refund_duplicate":
        return [step("S1", "refund_duplicate", f"duplicate payment of {amount} confirmed on {source}",
                     f"refund duplicate {amount} to {target}", amount,
                     f"refund of {amount} issued to {target} and duplicate cleared",
                     f"reclaim/void the {amount} refund", target, -amount)]
    return []


def build_plan(doc: dict) -> dict:
    errors, _ = _validate(doc)
    plan_id = f"PLAN-{doc.get('exception_id','UNKNOWN')}"
    if errors:
        return {"plan_id": plan_id, "status": "rejected", "reasons": errors,
                "approval": {"status": "n/a"}, "execution": {"state": "blocked", "executed_steps": []},
                "standing_note": STANDING_NOTE}

    etype = doc["type"]
    cat = CATALOG[etype]
    rem = doc["proposed_remedy"]
    amount = float(rem["amount"])
    target = rem["target"]
    source = rem.get("source") or "suspense"
    steps = _steps(plan_id, etype, cat["action"], amount, target, source)

    post_state = {}
    for s in steps:
        for acct, d in s["post_delta"].items():
            post_state[acct] = round(post_state.get(acct, 0) + d, 2)

    core = {"exception_id": doc["exception_id"], "loan_id": doc["loan_id"], "remedy": cat["action"],
            "amount": amount, "target": target, "steps": steps, "expected_post_state": post_state}
    plan_hash = hashlib.sha256(json.dumps(core, sort_keys=True).encode()).hexdigest()

    return {
        "plan_id": plan_id, "status": "planned",
        "exception_id": doc["exception_id"], "loan_id": doc["loan_id"],
        "catalog_version": doc.get("catalog_version"),
        "remedy": cat["action"], "amount": amount, "target": target,
        "authority_limit": cat["limit"], "reversible": cat["reversible"],
        "preconditions": [s["precondition"] for s in steps],
        "steps": steps, "expected_post_state": post_state,
        "plan_hash": plan_hash,
        "approval": {"required_role": cat["approver"], "status": "pending",
                     "approver": None, "approver_role": None, "token": None},
        "execution": {"state": "blocked", "executed_steps": []},
        "standing_note": STANDING_NOTE,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "exception_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(build_plan(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
