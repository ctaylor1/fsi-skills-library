#!/usr/bin/env python3
"""Deterministic repair-plan builder for payment-repair-assistant.

Builds a validated, idempotent repair plan from an approved payment-exception case + a
permissible repair. The plan is created BLOCKED and PENDING approval; this script never
resubmits, releases, returns, or cancels a payment. Execution is a separate, approval-gated
operation. Each step carries an idempotency key bound to the payment's end-to-end id so a
retried resubmission cannot create a duplicate payment.

Usage: python calculate_or_transform.py case.json | --selftest
Prints the plan JSON to stdout. A repair outside the catalog/limit, missing evidence, or an
uncleared screening yields a REJECTED plan (no steps, blocked).
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

from importlib import import_module
sys.path.insert(0, str(Path(__file__).resolve().parent))
CATALOG = import_module("validate_input").CATALOG  # single source of truth
_validate = import_module("validate_input").validate

STANDING_NOTE = ("Plan only; no payment has been resubmitted, released, returned, or "
                 "cancelled. Execution requires human approval.")


def _idem(plan_id, step_id, action, amount, ref):
    raw = f"{plan_id}|{step_id}|{action}|{amount}|{ref}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _step(plan_id, sid, act, amount, ref, pre, effect, verify, rollback,
          delta_key=None, delta=None, e2e=None):
    s = {"step_id": sid, "action": act,
         "idempotency_key": _idem(plan_id, sid, act, amount, ref),
         "precondition": pre, "expected_effect": effect, "effect_amount": amount,
         "verification": verify, "rollback": rollback,
         "post_delta": {delta_key: delta} if delta_key else {}}
    if e2e is not None:
        s["end_to_end_id"] = e2e  # binds the movement step to the original payment (dedup)
    return s


def _steps(plan_id, action, amount, currency, field, target, rail, e2e):
    if action in ("repair_and_resubmit", "release_and_resubmit"):
        if action == "repair_and_resubmit":
            s1 = _step(plan_id, "S1", "apply_repair", amount, field,
                       f"payment is held in the repair queue with {field} invalid or missing",
                       f"correct {field} to the verified value and re-validate the ISO 20022 message",
                       f"{field} re-validates against scheme rules; screening remains clear; no other field changed",
                       f"withdraw the repaired message from the resubmission queue and restore the original {field}")
        else:
            s1 = _step(plan_id, "S1", "release_hold", amount, "hold",
                       "payment is held pending screening and the disposition is a cleared false positive",
                       "release the screening hold on the payment",
                       "hold released; screening disposition recorded; message content unchanged",
                       "re-apply the screening hold")
        s2 = _step(plan_id, "S2", "resubmit_payment", amount, e2e,
                   f"repair applied, screening clear, and payment not already resubmitted (end-to-end id {e2e})",
                   f"resubmit the {currency} {amount} payment to {rail} under the original end-to-end id {e2e}",
                   f"payment accepted with a new status; exactly one submission confirmed for {e2e} (no duplicate)",
                   f"send a recall/return request (camt.056) for {e2e} before settlement",
                   delta_key="resubmitted_amount", delta=amount, e2e=e2e)
        return [s1, s2], "resubmitted"
    if action == "return_to_originator":
        s1 = _step(plan_id, "S1", "return_payment", amount, e2e,
                   f"payment {e2e} is an unrecoverable reject and has not already been returned",
                   f"return the {currency} {amount} payment to the originator (pacs.004) under end-to-end id {e2e}",
                   f"return accepted; exactly one return confirmed for {e2e} (no duplicate)",
                   "re-initiate the original payment only if the return was issued in error",
                   delta_key="returned_amount", delta=amount, e2e=e2e)
        return [s1], "returned"
    return [], "unknown"


def build_plan(doc: dict) -> dict:
    errors, _ = _validate(doc)
    plan_id = f"PLAN-{doc.get('case_id', 'UNKNOWN')}"
    if errors:
        return {"plan_id": plan_id, "status": "rejected", "reasons": errors,
                "approval": {"status": "n/a"},
                "execution": {"state": "blocked", "executed_steps": []},
                "standing_note": STANDING_NOTE}

    etype = doc["type"]
    cat = CATALOG[etype]
    rem = doc["proposed_repair"]
    amount = float(rem["amount"])
    currency = rem.get("currency") or "USD"
    target = rem["target"]
    field = rem.get("field") or target
    rail = rem.get("rail") or doc.get("rail") or "UNSPECIFIED"
    e2e = doc["end_to_end_id"]

    steps, expected_status = _steps(plan_id, cat["action"], amount, currency, field, target, rail, e2e)

    post_state = {}
    for s in steps:
        for acct, d in s["post_delta"].items():
            post_state[acct] = round(post_state.get(acct, 0) + d, 2)

    core = {"case_id": doc["case_id"], "payment_id": doc["payment_id"], "repair": cat["action"],
            "amount": amount, "target": target, "steps": steps, "expected_post_state": post_state}
    plan_hash = hashlib.sha256(json.dumps(core, sort_keys=True).encode()).hexdigest()

    return {
        "plan_id": plan_id, "status": "planned",
        "case_id": doc["case_id"], "payment_id": doc["payment_id"],
        "catalog_version": doc.get("catalog_version"),
        "repair": cat["action"], "amount": amount, "currency": currency,
        "target": target, "field": field, "rail": rail, "end_to_end_id": e2e,
        "authority_limit": cat["limit"], "reversible": cat["reversible"],
        "screening_required": cat["screening"], "screening": doc.get("screening") or {},
        "preconditions": [s["precondition"] for s in steps],
        "steps": steps, "expected_post_state": post_state, "expected_status": expected_status,
        "plan_hash": plan_hash,
        "approval": {"required_role": cat["approver"], "status": "pending", "approver": None, "token": None},
        "execution": {"state": "blocked", "executed_steps": []},
        "standing_note": STANDING_NOTE,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "case_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(build_plan(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
