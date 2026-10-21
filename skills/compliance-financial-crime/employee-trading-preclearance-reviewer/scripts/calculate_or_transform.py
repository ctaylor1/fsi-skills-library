#!/usr/bin/env python3
"""Produce an offline, source-bound employee-trade review plan; no execution adapter exists."""
from __future__ import annotations
import json, sys, importlib.util
from pathlib import Path
from native_integrity import attach_source, canonical_hash
_spec = importlib.util.spec_from_file_location(__name__ + "_input", Path(__file__).with_name("validate_input.py"))
_vi = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_vi)
STANDING_NOTE = "Review plan only. No preclearance decision, clearance, notification or system change has been made. This package cannot authenticate approvals or execute a plan. An authorized compliance owner must decide using refreshed evidence."

def build_plan(doc):
    errors, warnings = _vi.validate(doc)
    if errors: raise ValueError("; ".join(errors))
    policy = doc["policy"]
    notional = doc["notional_usd"]
    blocks, watch = _vi.derive_hard_blocks(doc), _vi.watch_hit(doc)
    if blocks: decision = "deny"
    elif notional > policy["senior_notional_limit_usd"]: decision = "escalate"
    elif watch or notional > policy["standard_notional_limit_usd"]: decision = "approve_with_conditions"
    else: decision = "approve"
    role = policy["standard_approver_role"] if decision == "approve" else policy["senior_approver_role"]
    conditions = []
    window = None
    if decision in ("approve", "approve_with_conditions"):
        if doc["side"] == "buy" and policy["min_holding_days"]: conditions.append(f"institution_min_holding_days:{policy['min_holding_days']}")
        if watch: conditions.append("watch_list_review")
        session = min((s for s in doc["trading_calendar"]["sessions"] if s["session_date"] > doc["request_date"]), key=lambda s: s["session_date"])
        window = {"proposed_from": doc["requested_at"], "proposed_until": session["close_at"],
                  "basis": "next session in supplied calendar; schedule/source truth unverified", "calendar_version": doc["trading_calendar"]["version"]}
    result = {"plan_id": "PLAN-" + canonical_hash(doc)[:16], "status": "review-plan", "action_mode": "plan-only",
        "request_id": doc["request_id"], "employee_id": doc["employee_id"], "account_id": doc["account_id"],
        "policy_version": doc["policy_version"], "policy_source_ref": policy["source_ref"],
        "request_date": doc["request_date"], "requested_at": doc["requested_at"], "instrument": doc["instrument"],
        "side": doc["side"], "quantity": doc["quantity"], "notional_usd": notional,
        "decision": decision, "decision_status": "recommendation_only", "hard_blocks": blocks, "watch_list_hit": watch,
        "screen_snapshot_refs": {name: {key: value for key, value in screen.items() if key in ("source_ref", "snapshot_id", "screened_at", "account_id")} for name, screen in doc["screens"].items()},
        "conditions": conditions, "proposed_clearance_window": window,
        "review_steps": ["Confirm account, employee, instrument and applicable institution policy.", "Verify source authenticity and refresh every mandatory screen before the human decision.", "Review the suggested disposition and calendar; record any decision only in the separately governed human workflow."],
        "approval": {"required_role": role, "status": "pending-human-review", "authenticated": False},
        "execution": {"state": "unsupported", "executed_steps": []}, "warnings": warnings, "standing_note": STANDING_NOTE}
    result["plan_hash"] = canonical_hash({"input_hash": canonical_hash(doc), "plan": result})
    return attach_source(result, doc)

compute = build_plan

def main(argv):
    p = Path(__file__).resolve().parents[1]/"evals/files/request_example.json" if "--selftest" in argv else Path(argv[0]) if argv else None
    try: result = build_plan(json.loads(p.read_text() if p else sys.stdin.read()))
    except (ValueError, TypeError, OSError) as exc:
        print("ERROR", exc, file=sys.stderr); return 1
    print(json.dumps(result, indent=2, allow_nan=False)); return 0
if __name__ == "__main__": raise SystemExit(main(sys.argv[1:]))
