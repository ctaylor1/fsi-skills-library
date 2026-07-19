#!/usr/bin/env python3
"""Deterministic resolution-plan builder for omnichannel-case-orchestrator.

Builds a validated, idempotent, multi-action resolution plan from a confirmed service
case + its permissible actions. The plan is created BLOCKED and PENDING approval; this
script never executes, posts, moves money, changes an account, or sends an outbound
commitment. Execution is a separate, approval-gated operation.

Usage: python calculate_or_transform.py case.json | --selftest
Prints the plan JSON to stdout. Any action outside the catalog / over its limit, or a plan
over the authority cap, yields a REJECTED plan with reasons and nothing to execute.
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

from importlib import import_module
sys.path.insert(0, str(Path(__file__).resolve().parent))
_vi = import_module("validate_input")
CATALOG = _vi.CATALOG            # single source of truth
PLAN_AUTHORITY_CAP = _vi.PLAN_AUTHORITY_CAP
ROLE_RANK = _vi.ROLE_RANK
_validate = _vi.validate

STANDING_NOTE = ("Plan only; no system-of-record change has been executed. "
                 "Execution requires human approval.")


def _idem(plan_id, action_id, action, amount, target):
    raw = f"{plan_id}|{action_id}|{action}|{amount}|{target}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _build_step(plan_id, a, cat):
    """One idempotent, verifiable, reversible step for a single permissible action."""
    aid = a["action_id"]
    action = cat["action"]
    target = a["target"]
    amount = round(float(a["amount"]), 2)

    if action == "waive_fee":
        pre = f"fee of {amount} is currently assessed on {target}"
        effect = f"waive {amount} fee on {target}"
        verify = f"{target} balance reduced by {amount}"
        rollback = f"re-assess the {amount} fee on {target}"
        delta = -amount
    elif action == "issue_goodwill_credit":
        pre = f"goodwill matrix permits {amount} credit for the recorded reason code"
        effect = f"issue {amount} goodwill credit to {target}"
        verify = f"{target} credited by {amount}"
        rollback = f"reverse the {amount} goodwill credit to {target}"
        delta = +amount
    elif action == "refund_overcharge":
        pre = f"overcharge of {amount} is confirmed on {target}"
        effect = f"refund {amount} overcharge to {target}"
        verify = f"refund of {amount} issued to {target}"
        rollback = f"reclaim/void the {amount} refund to {target}"
        delta = +amount
    elif action == "update_contact_preference":
        pre = f"identity is verified and the prior value of {target} is recorded"
        effect = f"set {target} to the requested value"
        verify = f"{target} equals the requested value"
        rollback = f"restore {target} to the prior recorded value"
        delta = a.get("new_value", "updated")
    elif action == "send_resolution_confirmation":
        pre = f"approved template and customer consent are on file for {target}"
        effect = f"send resolution confirmation via {target}"
        verify = f"confirmation to {target} recorded as sent"
        rollback = f"send a correction/retraction notice for {target}"
        delta = "sent"
    else:
        return None

    return {
        "step_id": aid, "action_type": a["type"], "action": action,
        "idempotency_key": _idem(plan_id, aid, action, amount, target),
        "precondition": pre, "expected_effect": effect,
        "effect_amount": amount if cat["monetary"] else 0,
        "verification": verify, "rollback": rollback,
        "post_delta": {target: delta},
    }


def build_plan(doc: dict) -> dict:
    errors, _ = _validate(doc)
    plan_id = f"PLAN-{doc.get('case_id', 'UNKNOWN')}"
    if errors:
        return {"plan_id": plan_id, "status": "rejected", "reasons": errors,
                "approval": {"status": "n/a"},
                "execution": {"state": "blocked", "executed_steps": []},
                "standing_note": STANDING_NOTE}

    actions_summary, steps = [], []
    total_exposure = 0.0
    max_rank, required_role = 0, None
    for a in doc["proposed_actions"]:
        cat = CATALOG[a["type"]]
        amount = round(float(a["amount"]), 2)
        actions_summary.append({
            "action_id": a["action_id"], "type": a["type"], "action": cat["action"],
            "amount": amount, "authority_limit": cat["limit"],
            "monetary": cat["monetary"], "reversible": cat["reversible"],
            "target": a["target"],
        })
        steps.append(_build_step(plan_id, a, cat))
        if cat["monetary"]:
            total_exposure += amount
        rank = ROLE_RANK.get(cat["approver"], 0)
        if rank > max_rank:
            max_rank, required_role = rank, cat["approver"]

    post_state = {}
    for s in steps:
        for acct, d in s["post_delta"].items():
            if isinstance(d, (int, float)):
                post_state[acct] = round(post_state.get(acct, 0) + d, 2)
            else:
                post_state[acct] = d

    # required_role is part of the hashed core so the approver tier is tamper-protected:
    # downgrading it after planning breaks the hash and voids the approval.
    core = {"case_id": doc["case_id"], "customer_id": doc["customer_id"],
            "actions": actions_summary, "steps": steps,
            "expected_post_state": post_state,
            "plan_authority_cap": PLAN_AUTHORITY_CAP,
            "required_role": required_role}
    plan_hash = hashlib.sha256(json.dumps(core, sort_keys=True).encode()).hexdigest()

    return {
        "plan_id": plan_id, "status": "planned",
        "case_id": doc["case_id"], "customer_id": doc["customer_id"],
        "channels": doc.get("channels"), "catalog_version": doc.get("catalog_version"),
        "actions": actions_summary,
        "total_monetary_exposure": round(total_exposure, 2),
        "plan_authority_cap": PLAN_AUTHORITY_CAP,
        "required_role": required_role,
        "preconditions": [s["precondition"] for s in steps],
        "steps": steps, "expected_post_state": post_state,
        "plan_hash": plan_hash,
        # approval.plan_hash is null until approval; at approval time the approver binds
        # the token to this exact plan_hash, so a token approved for a different plan cannot
        # be replayed to authorize this one.
        "approval": {"required_role": required_role, "status": "pending",
                     "approver": None, "approver_role": None, "token": None,
                     "plan_hash": None},
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
