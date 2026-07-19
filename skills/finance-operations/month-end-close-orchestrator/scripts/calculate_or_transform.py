#!/usr/bin/env python3
"""Deterministic close-plan builder for month-end-close-orchestrator.

Builds a validated, idempotent close-execution plan from a close-run request: the requested
close actions (accrual/reclass/allocation journals, reconciliation and task certifications,
sub-ledger and period locks) are topologically ordered by their dependencies into steps.

The plan is created BLOCKED and PENDING approval. This script never posts a journal,
certifies a task, or locks a period; execution is a separate, approval-gated operation.
Each step carries an idempotency key, a precondition (dependency + state read), an expected
effect, a verification read, and a rollback. The plan also carries an expected post-state
and a plan hash that binds the approval token.

Usage: python calculate_or_transform.py close_run.json | --selftest
Prints the plan JSON to stdout. An invalid request yields a REJECTED plan (no steps, blocked).
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

from importlib import import_module
sys.path.insert(0, str(Path(__file__).resolve().parent))
_vi = import_module("validate_input")
CATALOG = _vi.CATALOG                 # single source of truth
ROLE_RANK = _vi.ROLE_RANK
_validate = _vi.validate

STANDING_NOTE = ("Plan only; no journal has been posted and no task, reconciliation, or "
                 "period has been certified or locked. Execution requires human approval.")


def _idem(plan_id, step_id, action, amount, target):
    raw = f"{plan_id}|{step_id}|{action}|{amount}|{target}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _toposort(tasks: dict) -> list[str]:
    """Kahn's algorithm; ties broken by task_id for a deterministic order."""
    indeg = {t: 0 for t in tasks}
    for t, spec in tasks.items():
        for dep in spec.get("depends_on") or []:
            if dep in tasks:
                indeg[t] += 1
    ready = sorted(t for t, d in indeg.items() if d == 0)
    order: list[str] = []
    while ready:
        n = ready.pop(0)
        order.append(n)
        for t, spec in tasks.items():
            if n in (spec.get("depends_on") or []) and t not in order:
                indeg[t] -= 1
                if indeg[t] == 0:
                    ready.append(t)
        ready.sort()
    return order  # incomplete only if there is a cycle (already rejected upstream)


def _step(plan_id, task, seq):
    """Build one ordered, idempotent, reversible step from a requested close action."""
    tid = task["task_id"]
    action = task["action"]
    cat = CATALOG[action]
    target = task["target"]
    deps = list(task.get("depends_on") or [])
    step_id = f"S{seq}"
    dep_note = (" after " + ", ".join(deps)) if deps else ""

    if cat["kind"] == "journal":
        amount = round(float(task["amount"]), 2)
        offset = task.get("offset") or "GL:offset-clearing"
        return {
            "step_id": step_id, "task_id": tid, "action": action, "kind": "journal",
            "target": target,
            "idempotency_key": _idem(plan_id, step_id, action, amount, target),
            "precondition": f"period is open and {target} is postable{dep_note}",
            "expected_effect": f"post {amount} to {target} (offset {offset})",
            "effect_amount": amount,
            "verification": f"GL shows journal for {amount} posted to {target} under this idempotency key",
            "rollback": f"post the reversing journal for {amount} against {target}",
            "depends_on": deps,
            "post_delta": {target: amount, offset: -amount},
        }, {target: amount, offset: -amount}

    if cat["kind"] == "certify":
        flag = "certified"
        step = {
            "step_id": step_id, "task_id": tid, "action": action, "kind": "certify",
            "target": target,
            "idempotency_key": _idem(plan_id, step_id, action, "certify", target),
            "precondition": f"{target} is complete with evidence attached and zero unresolved breaks{dep_note}",
            "expected_effect": f"record certification sign-off on {target}",
            "effect_amount": None,
            "verification": f"close system shows {target} certified with actor and timestamp",
            "rollback": f"rescind the certification sign-off on {target}",
            "depends_on": deps,
            "post_delta": {target: flag},
        }
        # Carry the zero-breaks attestation onto the step so validate_output can enforce the
        # "never certify a reconciliation with unresolved breaks" boundary on the plan itself
        # (input validation already guaranteed this is 0 for a permissible build).
        if action == "certify_reconciliation":
            step["unresolved_breaks"] = int((task.get("evidence") or {}).get("unresolved_breaks", 0))
        return step, {target: flag}

    # lock (lock_subledger / close_period)
    flag = "closed" if action == "close_period" else "locked"
    return {
        "step_id": step_id, "task_id": tid, "action": action, "kind": "lock",
        "target": target,
        "idempotency_key": _idem(plan_id, step_id, action, "lock", target),
        "precondition": f"all prerequisite steps verified and {target} is not already {flag}{dep_note}",
        "expected_effect": f"set {target} to {flag} for the period",
        "effect_amount": None,
        "verification": f"period-control system shows {target} = {flag}",
        "rollback": f"re-open {target} (reverse the {flag} state)",
        "depends_on": deps,
        "post_delta": {target: flag},
    }, {target: flag}


def build_plan(doc: dict) -> dict:
    errors, _ = _validate(doc)
    plan_id = f"PLAN-{doc.get('close_run_id', 'UNKNOWN')}"
    if errors:
        return {"plan_id": plan_id, "status": "rejected", "reasons": errors,
                "approval": {"status": "n/a"},
                "execution": {"state": "blocked", "executed_steps": []},
                "standing_note": STANDING_NOTE}

    tasks = {t["task_id"]: t for t in doc["tasks"]}
    order = _toposort(tasks)

    steps = []
    post_state: dict = {}
    required_rank = 0
    required_role = "close-manager"
    for seq, tid in enumerate(order, start=1):
        step, delta = _step(plan_id, tasks[tid], seq)
        steps.append(step)
        for acct, d in delta.items():
            if isinstance(d, (int, float)):
                post_state[acct] = round(float(post_state.get(acct, 0)) + d, 2)
            else:
                post_state[acct] = d
        rank = ROLE_RANK.get(CATALOG[tasks[tid]["action"]]["approver"], 0)
        if rank > required_rank:
            required_rank, required_role = rank, CATALOG[tasks[tid]["action"]]["approver"]

    # Map each task_id to the step_id that realizes it, so dependencies are checkable by step.
    tid_to_step = {s["task_id"]: s["step_id"] for s in steps}
    for s in steps:
        s["depends_on_steps"] = [tid_to_step[d] for d in s["depends_on"] if d in tid_to_step]

    core = {"close_run_id": doc["close_run_id"], "entity": doc["entity"], "period": doc["period"],
            "steps": steps, "expected_post_state": post_state}
    plan_hash = hashlib.sha256(json.dumps(core, sort_keys=True).encode()).hexdigest()

    return {
        "plan_id": plan_id, "status": "planned",
        "close_run_id": doc["close_run_id"], "entity": doc["entity"], "period": doc["period"],
        "catalog_version": doc.get("catalog_version"),
        "step_order": [s["step_id"] for s in steps],
        "steps": steps, "expected_post_state": post_state,
        "plan_hash": plan_hash,
        "approval": {"required_role": required_role, "status": "pending", "approver": None, "token": None},
        "execution": {"state": "blocked", "executed_steps": []},
        "standing_note": STANDING_NOTE,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "close_run_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(build_plan(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
