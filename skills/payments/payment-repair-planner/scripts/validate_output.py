#!/usr/bin/env python3
"""Validate an offline plan against its full source request. Reject all execution/approval claims."""
from __future__ import annotations
import json
import sys
from pathlib import Path
from calculate_or_transform import build_plan, plan_hash


def validate(plan):
    if not isinstance(plan, dict):
        return ["plan must be an object"]
    errors = []
    execution, approval = plan.get("execution") or {}, plan.get("approval") or {}
    if (execution != {"state": "blocked", "executed_steps": []} or plan.get("execution_supported") is not False
            or any(s.get("execution_state") != "not_executed" for s in plan.get("steps", []))):
        errors.append("offline planner rejects execution claims; no executor exists")
    if approval.get("status") != "pending" or approval.get("token") is not None or approval.get("approver") is not None:
        errors.append("offline planner rejects approval claims and tokens; no approval verifier exists")
    if not isinstance(plan.get("plan_hash"), str) or not plan["plan_hash"]:
        errors.append("plan_hash missing or empty")
    elif plan_hash(plan) != plan["plan_hash"]:
        errors.append("plan_hash does not match complete plan contents")
    request = plan.get("source_request")
    if not isinstance(request, dict):
        errors.append("source_request required to validate exact change and scoped policy")
    else:
        try:
            expected = build_plan(request)
            for key in set(expected) | set(plan):
                if expected.get(key) != plan.get(key):
                    errors.append(f"{key} differs from source-bound offline plan")
        except (ValueError, TypeError, KeyError) as exc:
            errors.append(f"invalid source request: {exc}")
    return errors


def main(argv):
    path = Path(__file__).resolve().parents[1] / "evals/files/plan_example.json" if "--selftest" in argv else (Path(argv[0]) if argv else None)
    errors = validate(json.loads(path.read_text() if path else sys.stdin.read()))
    for item in errors: print("ERROR", item)
    print(f"output validation: {len(errors)} error(s)")
    return bool(errors)

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
