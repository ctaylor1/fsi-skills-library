#!/usr/bin/env python3
"""Deterministic preclearance decision-plan builder for employee-trading-preclearance-assistant.

Builds a validated, idempotent DECISION PLAN from a personal-trade preclearance request. The
plan records the recommended decision (approve / approve_with_conditions / deny) and the
ordered steps that would write it (record decision, issue clearance window, apply conditions,
append audit) — each step with an idempotency key, precondition, verification, and rollback,
plus an aggregated expected post-state and a tamper-evident plan hash.

The plan is created BLOCKED and PENDING approval. This script NEVER records a decision,
issues a clearance, or changes a system of record. Execution is a separate, approval-gated
operation that requires a valid human approval token bound to the plan hash.

HARD BOUNDARY: a request that hits a hard block (restricted list, active blackout,
minimum-holding breach, or a conflict/MNPI flag) can only produce a `deny` decision — the
builder will never emit an `approve*` plan for it. A notional above the senior authority
limit yields a REJECTED plan that escalates to the Chief Compliance Officer.

Usage: python calculate_or_transform.py request.json | --selftest
Prints the plan JSON to stdout.
"""
from __future__ import annotations
import hashlib, json, sys
from datetime import date, timedelta
from pathlib import Path

from importlib import import_module
sys.path.insert(0, str(Path(__file__).resolve().parent))
_vi = import_module("validate_input")  # single source of truth for policy constants
CATALOG = _vi.DECISION_LIMITS
CCO_ESCALATION_ABOVE = _vi.CCO_ESCALATION_ABOVE
MIN_HOLDING_DAYS = _vi.MIN_HOLDING_DAYS

STANDING_NOTE = ("Decision plan only; no preclearance decision has been recorded and no "
                 "clearance has been issued. Execution requires compliance approval.")


def _idem(plan_id, step_id, action, detail):
    raw = f"{plan_id}|{step_id}|{action}|{detail}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _next_day(iso: str) -> str:
    try:
        y, m, d = (int(x) for x in iso.split("-"))
        return (date(y, m, d) + timedelta(days=1)).isoformat()
    except Exception:
        return iso


def _step(plan_id, sid, action, pre, effect, verify, rollback, post_state, extra=None):
    s = {"step_id": sid, "action": action,
         "idempotency_key": _idem(plan_id, sid, action, json.dumps(post_state, sort_keys=True)),
         "precondition": pre, "expected_effect": effect,
         "verification": verify, "rollback": rollback, "post_state": post_state}
    if extra:
        s.update(extra)
    return s


def _approve_steps(plan_id, rid, decision, notional, window, conditions):
    steps = [
        _step(plan_id, "S1", "record_decision",
              f"no prior open preclearance decision exists for {rid}",
              f"record decision '{decision}' for {rid} in the preclearance register",
              f"preclearance register shows decision '{decision}' for {rid} with matching plan_hash",
              f"void/withdraw the recorded decision for {rid}",
              {f"register:{rid}:decision": decision}),
        _step(plan_id, "S2", "issue_clearance_window",
              f"decision '{decision}' recorded for {rid}",
              f"issue clearance window {window['valid_from']}..{window['valid_to']} authorizing up to {notional} notional",
              f"active, unexpired clearance window present for {rid}",
              f"revoke the clearance window for {rid}",
              {f"register:{rid}:clearance_state": "cleared"},
              extra={"cleared_notional": notional, "clearance_window": window}),
    ]
    if conditions:
        steps.append(_step(plan_id, "S3", "apply_conditions",
              f"active clearance window for {rid}",
              f"apply conditions {conditions} to the clearance for {rid}",
              f"conditions {conditions} recorded against {rid}",
              f"remove conditions {conditions} from {rid}",
              {f"register:{rid}:conditions": ",".join(conditions)}))
    steps.append(_step(plan_id, "S4", "append_audit",
              f"decision '{decision}' recorded for {rid}",
              f"append the preclearance decision event for {rid} to the compliance audit log",
              f"audit log contains an immutable entry for {rid} carrying the plan_hash",
              f"audit log is append-only; a compensating annotation records any reversal for {rid}",
              {f"audit:{rid}": "appended"}))
    return steps


def _deny_steps(plan_id, rid, reasons):
    return [
        _step(plan_id, "S1", "record_decision",
              f"no prior open preclearance decision exists for {rid}",
              f"record decision 'deny' for {rid} in the preclearance register (reasons: {reasons})",
              f"preclearance register shows decision 'deny' for {rid} with matching plan_hash",
              f"withdraw the denial and reopen {rid}",
              {f"register:{rid}:decision": "deny"}),
        _step(plan_id, "S2", "notify_and_close",
              f"decision 'deny' recorded for {rid}",
              f"notify the employee that {rid} is denied and close the request as denied",
              f"request {rid} closed as denied and employee notified",
              f"reopen {rid} and retract the denial notice",
              {f"register:{rid}:clearance_state": "denied"}),
        _step(plan_id, "S3", "append_audit",
              f"decision 'deny' recorded for {rid}",
              f"append the denial decision event for {rid} to the compliance audit log",
              f"audit log contains an immutable entry for {rid} carrying the plan_hash",
              f"audit log is append-only; a compensating annotation records any reversal for {rid}",
              {f"audit:{rid}": "appended"}),
    ]


def _core(doc, decision, conditions, steps, post_state):
    return {"request_id": doc["request_id"], "employee_id": doc["employee_id"],
            "instrument": doc["instrument"], "side": doc["side"],
            "quantity": doc["quantity"], "notional_usd": float(doc["notional_usd"]),
            "decision": decision, "conditions": conditions,
            "steps": steps, "expected_post_state": post_state}


def build_plan(doc: dict) -> dict:
    errors, _ = _vi.validate(doc)
    rid = doc.get("request_id", "UNKNOWN")
    plan_id = f"PLAN-{rid}"
    if errors:
        return {"plan_id": plan_id, "status": "rejected", "reasons": errors,
                "approval": {"status": "n/a"},
                "execution": {"state": "blocked", "executed_steps": []},
                "standing_note": STANDING_NOTE}

    notional = float(doc["notional_usd"])
    hard_blocks = _vi.derive_hard_blocks(doc)
    watch = _vi.watch_hit(doc)

    # Deterministic decision derivation. Hard blocks always force deny.
    if hard_blocks:
        decision = "deny"
    elif notional > CCO_ESCALATION_ABOVE:
        return {"plan_id": plan_id, "status": "rejected",
                "reasons": [f"notional {notional} exceeds the senior authority limit "
                            f"{CCO_ESCALATION_ABOVE} — escalate to the Chief Compliance Officer "
                            f"(out of scope for auto-planning)"],
                "approval": {"status": "n/a"},
                "execution": {"state": "blocked", "executed_steps": []},
                "standing_note": STANDING_NOTE}
    elif watch or notional > CATALOG["approve"]["notional_limit"]:
        decision = "approve_with_conditions"
    else:
        decision = "approve"

    cat = CATALOG[decision]
    conditions: list[str] = []

    if decision == "deny":
        steps = _deny_steps(plan_id, rid, hard_blocks)
    else:
        if doc["side"] == "buy":
            conditions.append(f"min_holding_lock:{MIN_HOLDING_DAYS}d")
        if watch:
            conditions.append("watch_list_monitoring")
        window = {"valid_from": doc["request_date"], "valid_to": _next_day(doc["request_date"]),
                  "horizon": "close of the next trading day"}
        steps = _approve_steps(plan_id, rid, decision, notional, window, conditions)

    post_state: dict = {}
    for s in steps:
        post_state.update(s["post_state"])

    core = _core(doc, decision, conditions, steps, post_state)
    plan_hash = hashlib.sha256(json.dumps(core, sort_keys=True).encode()).hexdigest()

    return {
        "plan_id": plan_id, "status": "planned",
        "request_id": rid, "employee_id": doc["employee_id"],
        "policy_version": doc.get("policy_version"),
        "instrument": doc["instrument"], "side": doc["side"],
        "quantity": doc["quantity"], "notional_usd": notional,
        "decision": decision, "hard_blocks": hard_blocks, "watch_list_hit": watch,
        "conditions": conditions,
        "authority_limit": cat["notional_limit"],
        "steps": steps, "expected_post_state": post_state,
        "plan_hash": plan_hash,
        "approval": {"required_role": cat["approver"], "status": "pending",
                     "approver": None, "approver_role": None, "token": None},
        "execution": {"state": "blocked", "executed_steps": []},
        "standing_note": STANDING_NOTE,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "request_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(build_plan(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
