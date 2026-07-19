#!/usr/bin/env python3
"""Deterministic trade-break repair-plan builder for trade-break-resolver.

Builds a validated, idempotent repair plan from a confirmed trade break + permissible
repair. The plan is created BLOCKED and PENDING approval; this script never executes,
amends, cancels, rebooks, or writes an OMS/EMS. Execution is a separate, approval-gated
operation.

Usage: python calculate_or_transform.py break.json | --selftest
Prints the plan JSON to stdout. A repair outside the catalog/limit yields a REJECTED plan.
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


def _steps(plan_id, action, amount, target, source):
    """Return ordered, idempotent, reversible steps + expected post-state deltas."""
    def step(sid, act, pre, effect, effect_amt, verify, rollback, acct, delta):
        return {"step_id": sid, "action": act,
                "idempotency_key": _idem(plan_id, sid, act, effect_amt, acct),
                "precondition": pre, "expected_effect": effect, "effect_amount": effect_amt,
                "verification": verify, "rollback": rollback,
                "post_delta": {acct: delta}}

    if action == "rebook_trade":
        s1 = step("S1", "cancel_source_booking",
                  f"trade is booked to {source} for notional {amount}",
                  f"remove {amount} notional from {source}", amount,
                  f"{source} exposure decreased by {amount}",
                  f"re-book {amount} notional to {source}", source, -amount)
        s2 = step("S2", "rebook_target",
                  f"book {target} is open for the corrected trade",
                  f"book {amount} notional to {target}", amount,
                  f"{target} exposure increased by {amount}",
                  f"reverse the {amount} booking on {target}", target, +amount)
        return [s1, s2]
    if action == "amend_quantity":
        return [step("S1", "amend_quantity",
                     f"trade {target} shows the pre-amendment quantity",
                     f"adjust {target} quantity by notional {amount}", amount,
                     f"{target} notional adjusted by {amount} to the confirmed quantity",
                     f"re-amend {target} to the prior quantity", target, +amount)]
    if action == "amend_price":
        return [step("S1", "amend_price",
                     f"trade {target} shows the pre-amendment price",
                     f"adjust settlement amount on {target} by {amount}", amount,
                     f"{target} settlement amount adjusted by {amount} to the agreed price",
                     f"re-amend {target} to the prior price", target, +amount)]
    if action == "cancel_trade":
        return [step("S1", "cancel_trade",
                     f"duplicate booking {target} of {amount} exists",
                     f"cancel duplicate booking {target} for {amount}", amount,
                     f"duplicate {target} removed; net exposure reduced by {amount}",
                     f"re-book the cancelled {amount} trade {target}", target, -amount)]
    return []


def build_plan(doc: dict) -> dict:
    errors, _ = _validate(doc)
    plan_id = f"PLAN-{doc.get('break_id', 'UNKNOWN')}"
    if errors:
        return {"plan_id": plan_id, "status": "rejected", "reasons": errors,
                "approval": {"status": "n/a"}, "execution": {"state": "blocked", "executed_steps": []},
                "standing_note": STANDING_NOTE}

    btype = doc["type"]
    cat = CATALOG[btype]
    rep = doc["proposed_repair"]
    amount = float(rep["amount"])
    target = rep["target"]
    source = rep.get("source") or "trade-blotter"
    steps = _steps(plan_id, cat["action"], amount, target, source)

    post_state = {}
    for s in steps:
        for acct, d in s["post_delta"].items():
            post_state[acct] = round(post_state.get(acct, 0) + d, 2)

    core = {"break_id": doc["break_id"], "trade_id": doc["trade_id"], "repair": cat["action"],
            "amount": amount, "target": target, "steps": steps, "expected_post_state": post_state}
    plan_hash = hashlib.sha256(json.dumps(core, sort_keys=True).encode()).hexdigest()

    return {
        "plan_id": plan_id, "status": "planned",
        "break_id": doc["break_id"], "trade_id": doc["trade_id"],
        "break_type": btype, "catalog_version": doc.get("catalog_version"),
        "repair": cat["action"], "amount": amount, "target": target,
        "authority_limit": cat["limit"], "reversible": cat["reversible"],
        "preconditions": [s["precondition"] for s in steps],
        "steps": steps, "expected_post_state": post_state,
        "plan_hash": plan_hash,
        "approval": {"required_role": cat["approver"], "status": "pending", "approver": None, "token": None},
        "execution": {"state": "blocked", "executed_steps": []},
        "standing_note": STANDING_NOTE,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "break_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(build_plan(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
