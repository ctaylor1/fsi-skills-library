#!/usr/bin/env python3
"""Build an R3 offline proposal; never approve, authenticate a token, or execute a payment."""
from __future__ import annotations
import copy
import json
import sys
from pathlib import Path
from payment_contract import stable_hash, money
from validate_input import validate as validate_input

STANDING_NOTE = ("Offline repair proposal only. No approval has been granted or authenticated and no payment "
                 "has been changed or submitted. A hash is an integrity identifier, not authorization. "
                 "Settlement cannot be rolled back; a recall or compensation may fail.")


def plan_hash(plan):
    return stable_hash({key: value for key, value in plan.items() if key != "plan_hash"})


def build_plan(doc):
    doc = copy.deepcopy(doc)
    errors, warnings = validate_input(doc)
    base = {"schema_version": "repair-plan-v1", "source_request": doc,
            "source_hash": stable_hash(doc), "plan_id": "PLAN-" + stable_hash(doc)[:20],
            "status": "rejected" if errors else "planned", "reasons": errors,
            "approval": {"status": "pending", "required_role": (doc.get("policy") or {}).get("required_approver_role"),
                         "approver": None, "token": None},
            "execution": {"state": "blocked", "executed_steps": []},
            "execution_supported": False, "authority_evidence": "supplied-not-authenticated",
            "steps": [], "limitations": warnings, "standing_note": STANDING_NOTE}
    if not errors:
        original, repair = doc["payment_snapshot"], doc["proposed_repair"]
        base.update({"case_id": doc["case_id"], "payment_id": doc["payment_id"],
                     "end_to_end_id": original["end_to_end_id"], "entity_id": original["entity_id"],
                     "rail": original["rail"], "currency": original["currency"],
                     "amount": str(money(original["amount"])), "catalog_version": doc["catalog_version"],
                     "policy": doc["policy"], "screening": doc["screening"],
                     "repair": "repair_and_resubmit", "field": repair["field"],
                     "exact_change": {"field": repair["field"], "before": repair["old_value"], "after": repair["new_value"]},
                     "unchanged_fields_hash": stable_hash({k: v for k, v in original.items() if k != "fields"} | {
                         "fields": {k: v for k, v in original["fields"].items() if k != repair["field"]}})})
        for index, action in enumerate(("apply_repair", "resubmit_payment"), 1):
            base["steps"].append({
                "step_id": f"S{index}", "action": action,
                "exact_change": base["exact_change"] if index == 1 else None,
                "payment_id": doc["payment_id"], "end_to_end_id": original["end_to_end_id"],
                "idempotency_scope": stable_hash({"entity": original["entity_id"], "rail": original["rail"],
                    "payment_id": doc["payment_id"], "end_to_end_id": original["end_to_end_id"], "action": action}),
                "precondition": "Authorized operator rechecks current state, screening, exact approval scope, prior attempts, and policy before acting.",
                "expected_effect": "Only the exact field change is proposed." if index == 1 else "A single submission may be accepted; settlement is not guaranteed.",
                "verification": "Compare full before/after instruction and obtain authoritative outcome; unknown outcome remains blocked for investigation.",
                "failure_handling": "Stop and investigate. No automatic retry, recall, or guaranteed rollback.",
                "execution_state": "not_executed"})
        base["expected_status"] = "proposal_only"
    base["plan_hash"] = plan_hash(base)
    return base


def main(argv):
    path = Path(__file__).resolve().parents[1] / "evals/files/case_example.json" if "--selftest" in argv else (Path(argv[0]) if argv else None)
    doc = json.loads(path.read_text() if path else sys.stdin.read())
    result = build_plan(doc)
    print(json.dumps(result, indent=2))
    return 1 if result["status"] == "rejected" else 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
