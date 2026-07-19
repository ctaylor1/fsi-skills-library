#!/usr/bin/env python3
"""Deterministic election-plan builder for corporate-action-election-assistant.

Builds a validated, idempotent election plan from a confirmed voluntary corporate action,
the eligible position, and a chosen option/legs. The plan is created BLOCKED and PENDING
approval; this script never submits, records, or confirms an election with a custodian or
agent. Submission is a separate, approval-gated operation.

Each step carries an idempotency key, precondition, expected effect, verification, and
rollback; the plan also records the expected post-state and a tamper-evident plan hash.

Usage: python calculate_or_transform.py election.json | --selftest
Prints the plan JSON to stdout. A request outside the catalog/limit/window yields a
REJECTED plan (no steps, blocked). Under --selftest it also self-checks the built plan and
prints a "plan self-check: N error(s)" line (exit 1 if the built plan fails validation).
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path
from importlib import import_module

sys.path.insert(0, str(Path(__file__).resolve().parent))
_vi = import_module("validate_input")
CATALOG = _vi.CATALOG            # single source of truth for the catalog
_validate = _vi.validate
_legs_of = _vi.legs_of
OVERSUB_OPTIONS = _vi.OVERSUB_OPTIONS

STANDING_NOTE = ("Plan only; no election has been submitted to the custodian or agent. "
                 "Submission requires human approval.")


def _idem(plan_id, step_id, option, quantity, account):
    raw = f"{plan_id}|{step_id}|{option}|{quantity}|{account}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _core(plan: dict) -> dict:
    """The subset of plan fields bound by the plan hash (tamper detection)."""
    return {
        "event_id": plan.get("event_id"), "account": plan.get("account"),
        "event_type": plan.get("event_type"), "election_action": plan.get("election_action"),
        "permissible_options": plan.get("permissible_options"), "basis": plan.get("basis"),
        "effective_cap": plan.get("effective_cap"),
        "instructed_quantity": plan.get("instructed_quantity"),
        "eligible_quantity": plan.get("eligible_quantity"),
        "reference_price": plan.get("reference_price"), "notional": plan.get("notional"),
        "authority_limit": plan.get("authority_limit"), "reversible": plan.get("reversible"),
        "as_of": plan.get("as_of"), "submission_deadline": plan.get("submission_deadline"),
        "legs": plan.get("legs"), "steps": plan.get("steps"),
        "expected_post_state": plan.get("expected_post_state"),
    }


def build_plan(doc: dict) -> dict:
    errors, _ = _validate(doc)
    plan_id = f"CAE-PLAN-{doc.get('event_id', 'UNKNOWN')}-{doc.get('account', 'UNKNOWN')}"
    if errors:
        return {"plan_id": plan_id, "status": "rejected", "reasons": errors,
                "approval": {"status": "n/a"},
                "execution": {"state": "blocked", "executed_steps": []},
                "standing_note": STANDING_NOTE}

    etype = doc["event_type"]
    cat = CATALOG[etype]
    account = doc["account"]
    event_id = doc["event_id"]
    eligible = float(doc["eligible_quantity"])
    price = float(doc["reference_price"])
    as_of = doc["as_of"]
    deadline = doc["submission_deadline"]
    legs, _ = _legs_of(doc["proposed_election"])
    legs = [{"option": l["option"], "quantity": float(l["quantity"])} for l in legs]
    instructed = round(sum(l["quantity"] for l in legs), 6)
    notional = round(instructed * price, 2)
    cap = cat["oversubscribe_cap"] if any(l["option"] in OVERSUB_OPTIONS for l in legs) else 1.0

    steps, post_state, cum = [], {}, 0.0
    for i, leg in enumerate(legs, start=1):
        sid = f"S{i}"
        opt, q = leg["option"], leg["quantity"]
        cum = round(cum + q, 6)
        steps.append({
            "step_id": sid, "action": "submit_option_leg",
            "idempotency_key": _idem(plan_id, sid, opt, q, account),
            "precondition": (f"as of {as_of} account {account} holds eligible {eligible}; "
                             f"cumulative instructed {cum} <= eligible {round(eligible * cap, 6)}; "
                             f"election window open until {deadline}; option '{opt}' permissible for {etype}"),
            "expected_effect": f"submit instruction to elect {q} under '{opt}' for event {event_id} / account {account}",
            "effect_quantity": q,
            "verification": (f"custodian/agent acknowledgment matches event {event_id}, account {account}, "
                             f"option '{opt}', quantity {q}"),
            "rollback": f"withdraw or supersede the '{opt}' election of {q} before {deadline}",
            "post_delta": {opt: q},
        })
        post_state[opt] = round(post_state.get(opt, 0.0) + q, 6)
    post_state["total_instructed"] = instructed

    plan = {
        "plan_id": plan_id, "status": "planned",
        "event_id": event_id, "interpretation_id": doc.get("interpretation_id"),
        "account": account, "event_type": etype,
        "catalog_version": doc.get("catalog_version"),
        "election_action": cat["action"], "permissible_options": list(cat["options"]),
        "basis": cat["basis"], "effective_cap": cap,
        "instructed_quantity": instructed, "eligible_quantity": eligible,
        "reference_price": price, "notional": notional,
        "authority_limit": cat["notional_limit"], "reversible": cat["reversible"],
        "as_of": as_of, "submission_deadline": deadline,
        "market_deadline": doc.get("market_deadline"),
        "legs": legs, "steps": steps, "expected_post_state": post_state,
        "approval": {"required_role": cat["approver"], "status": "pending",
                     "approver": None, "token": None},
        "execution": {"state": "blocked", "executed_steps": []},
        "standing_note": STANDING_NOTE,
    }
    plan["plan_hash"] = hashlib.sha256(json.dumps(_core(plan), sort_keys=True).encode()).hexdigest()
    return plan


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "election_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    plan = build_plan(doc)
    print(json.dumps(plan, indent=2))
    if "--selftest" in argv:
        _vo = import_module("validate_output")
        errs = _vo.validate(plan)
        for e in errs:
            print("ERROR", e)
        print(f"plan self-check: {len(errs)} error(s)")
        return 1 if errs else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
