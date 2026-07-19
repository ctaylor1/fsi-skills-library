#!/usr/bin/env python3
"""Deterministic correction-plan builder for accounts-payable-exception-resolver.

Builds a validated, idempotent correction plan from a confirmed AP exception + permissible
remedy. The plan is created BLOCKED and PENDING approval; this script never executes, posts,
disburses, or changes a system of record. Execution is a separate, approval-gated operation.

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


def _steps(plan_id, invoice, action, amount, target, source):
    """Return ordered, idempotent, reversible steps + expected post-state deltas.

    Money-value corrections (adjust/align/tax) net the delta between AP-subledger buckets.
    Hold/route actions place a protective control flag; no funds move under any action.
    """
    def step(sid, act, pre, effect, verify, rollback, acct, delta):
        return {"step_id": sid, "action": act,
                "idempotency_key": _idem(plan_id, sid, act, amount, acct),
                "precondition": pre, "expected_effect": effect, "effect_amount": amount,
                "verification": verify, "rollback": rollback,
                "post_delta": {acct: round(delta, 2)}}

    if action == "adjust_invoice_price":
        s1 = step("S1", "debit_ap_liability",
                  f"AP liability holds the {amount} price variance for {invoice}",
                  f"reduce AP liability by {amount}",
                  f"AP liability decreased by {amount}",
                  f"restore {amount} to AP liability", source, -amount)
        s2 = step("S2", "credit_price_variance",
                  f"price-variance account {target} is open",
                  f"post {amount} price variance to {target}",
                  f"{target} increased by {amount}",
                  f"reverse the {amount} posting to {target}", target, +amount)
        return [s1, s2]
    if action == "align_to_po_quantity":
        s1 = step("S1", "debit_ap_liability",
                  f"AP liability is over-billed by {amount} vs PO/receipt for {invoice}",
                  f"reduce AP liability by {amount}",
                  f"AP liability decreased by {amount}",
                  f"restore {amount} to AP liability", source, -amount)
        s2 = step("S2", "credit_gr_ir",
                  f"GR/IR clearing {target} is open",
                  f"move {amount} unmatched value to {target}",
                  f"{target} increased by {amount}",
                  f"reverse the {amount} move to {target}", target, +amount)
        return [s1, s2]
    if action == "match_to_receipt":
        return [step("S1", "hold_in_gr_ir",
                     f"invoice {invoice} matched value overstates the receipt by {amount}",
                     f"hold {amount} in GR/IR pending goods receipt",
                     f"AP liability reduced by {amount} pending receipt",
                     f"restore prior match ({amount} to AP liability)", source, -amount)]
    if action == "correct_tax_code":
        s1 = step("S1", "adjust_tax",
                  f"tax is miscoded on {invoice} by {amount}",
                  f"correct tax on {invoice} by {amount}",
                  f"{target} adjusted by {amount}",
                  f"restore prior tax code ({amount}) on {invoice}", target, -amount)
        s2 = step("S2", "offset_ap_liability",
                  f"AP liability reflects the miscoded tax on {invoice}",
                  f"offset AP liability by {amount}",
                  f"AP liability offset by {amount}",
                  f"reverse the {amount} AP offset", source, +amount)
        return [s1, s2]
    if action == "block_duplicate":
        return [step("S1", "place_payment_hold",
                     f"duplicate invoice of {amount} confirmed against {source} for {invoice}",
                     f"place payment hold on {invoice} for {amount} and flag duplicate",
                     f"payment_hold on {invoice} equals {amount}",
                     f"release the {amount} hold and unflag the duplicate", target, +amount)]
    if action == "hold_for_bank_verification":
        return [step("S1", "place_payment_hold",
                     f"supplier bank details on {invoice} differ from the master",
                     f"place protective payment hold on {invoice} for {amount} pending bank re-verification",
                     f"payment_hold on {invoice} equals {amount}",
                     f"release the {amount} hold after bank verification", target, +amount)]
    if action == "route_for_approval":
        return [step("S1", "place_approval_hold",
                     f"invoice {invoice} lacks the required approval per delegation of authority",
                     f"route {invoice} for approval ({amount}) and place approval hold",
                     f"approval_hold on {invoice} equals {amount}",
                     f"recall routing and release the {amount} approval hold", target, +amount)]
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
    source = rem.get("source") or "ap_liability"
    invoice = doc["invoice_id"]
    steps = _steps(plan_id, invoice, cat["action"], amount, target, source)

    post_state = {}
    for s in steps:
        for acct, d in s["post_delta"].items():
            post_state[acct] = round(post_state.get(acct, 0) + d, 2)

    core = {"exception_id": doc["exception_id"], "invoice_id": doc["invoice_id"],
            "vendor_id": doc["vendor_id"], "remedy": cat["action"], "amount": amount,
            "target": target, "steps": steps, "expected_post_state": post_state}
    plan_hash = hashlib.sha256(json.dumps(core, sort_keys=True).encode()).hexdigest()

    return {
        "plan_id": plan_id, "status": "planned",
        "exception_id": doc["exception_id"], "invoice_id": doc["invoice_id"],
        "vendor_id": doc["vendor_id"], "catalog_version": doc.get("catalog_version"),
        "remedy": cat["action"], "amount": amount, "target": target,
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
