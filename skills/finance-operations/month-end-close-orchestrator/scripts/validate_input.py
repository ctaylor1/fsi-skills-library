#!/usr/bin/env python3
"""Deterministic input validation for month-end-close-orchestrator.

Validates a close-run request (period, entity, and the requested close actions with their
dependency graph) BEFORE any plan is built. Fails closed on structural problems, an action
that is not in the permissible close-action catalog, a journal over its posting-authority
limit, missing evidence, an un-cleared reconciliation, a dangling/duplicate task id, or a
dependency cycle. Nothing here posts, certifies, or locks anything.

Input schema (JSON): see references/domain-rules.md. Key fields:
  close_run_id, entity, period, catalog_version,
  tasks[]: {task_id, action, target, amount?, depends_on[], evidence{...}}

Usage: python validate_input.py close_run.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

# Permissible close-action catalog (default; deployment supplies a versioned catalog).
#   kind:      journal (amount-bearing GL posting) | certify (sign-off) | lock (state change)
#   limit:     per-posting authority limit (journals only; None for non-amount actions)
#   reversible:every gated action must be reversible for auto-planning
#   approver:  minimum role that may approve this action
#   evidence:  required evidence keys before the action may be planned
CATALOG = {
    "post_accrual_journal":    {"kind": "journal", "limit": 250000,  "reversible": True,
                                "approver": "controller",    "evidence": ["support_schedule"]},
    "post_reclass_journal":    {"kind": "journal", "limit": 250000,  "reversible": True,
                                "approver": "controller",    "evidence": ["support_schedule"]},
    "post_allocation_journal": {"kind": "journal", "limit": 1000000, "reversible": True,
                                "approver": "controller",    "evidence": ["allocation_basis"]},
    "certify_reconciliation":  {"kind": "certify", "limit": None,    "reversible": True,
                                "approver": "close-manager", "evidence": ["reconciliation_ref"]},
    "certify_close_task":      {"kind": "certify", "limit": None,    "reversible": True,
                                "approver": "close-manager", "evidence": ["task_evidence"]},
    "lock_subledger":          {"kind": "lock",    "limit": None,    "reversible": True,
                                "approver": "controller",    "evidence": ["subledger_ref"]},
    "close_period":            {"kind": "lock",    "limit": None,    "reversible": True,
                                "approver": "controller",    "evidence": ["period_checklist"]},
}
# Approver seniority for the plan-level required role (highest wins).
ROLE_RANK = {"close-manager": 1, "controller": 2}
REQUIRED_TOP = ("close_run_id", "entity", "period", "tasks")


def _has_cycle(tasks: dict) -> list[str]:
    """Return a list of task_ids on a dependency cycle (empty if the graph is a DAG)."""
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {t: WHITE for t in tasks}
    onstack: list[str] = []

    def visit(node: str) -> list[str]:
        color[node] = GRAY
        onstack.append(node)
        for dep in tasks[node].get("depends_on") or []:
            if dep not in tasks:
                continue  # dangling dep reported separately
            if color[dep] == GRAY:
                return onstack[onstack.index(dep):]
            if color[dep] == WHITE:
                found = visit(dep)
                if found:
                    return found
        color[node] = BLACK
        onstack.pop()
        return []

    for t in tasks:
        if color[t] == WHITE:
            found = visit(t)
            if found:
                return found
    return []


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    tasks = doc.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        errors.append("'tasks' must be a non-empty list")
        return errors, warnings

    ids: dict[str, dict] = {}
    for i, t in enumerate(tasks):
        tid = t.get("task_id")
        if not tid:
            errors.append(f"tasks[{i}]: missing task_id")
            continue
        if tid in ids:
            errors.append(f"duplicate task_id {tid!r}")
            continue
        ids[tid] = t

    for tid, t in ids.items():
        action = t.get("action")
        cat = CATALOG.get(action)
        if not cat:
            errors.append(f"{tid}: action {action!r} not in permissible close-action catalog — escalate (out of scope)")
            continue
        if not t.get("target"):
            errors.append(f"{tid}: target is required")

        if cat["kind"] == "journal":
            amt = t.get("amount")
            try:
                amt = float(amt)
            except (TypeError, ValueError):
                errors.append(f"{tid}: {action} requires a numeric amount")
                amt = None
            if amt is not None:
                if amt <= 0:
                    errors.append(f"{tid}: amount must be > 0")
                if cat["limit"] is not None and amt > cat["limit"]:
                    errors.append(f"{tid}: amount {amt} exceeds posting-authority limit {cat['limit']} "
                                  f"for {action} — escalate (out of scope)")
        else:
            if t.get("amount") not in (None, 0):
                warnings.append(f"{tid}: {action} is not amount-bearing; amount is ignored")

        if not cat["reversible"]:
            errors.append(f"{tid}: {action} is not reversible — out of scope for auto-planning")

        ev = t.get("evidence") or {}
        missing_ev = [e for e in cat["evidence"] if not ev.get(e)]
        if missing_ev:
            errors.append(f"{tid}: missing required evidence for {action}: {', '.join(missing_ev)}")

        # A reconciliation may only be certified when it carries zero unresolved breaks.
        if action == "certify_reconciliation":
            ub = ev.get("unresolved_breaks")
            if ub is None:
                errors.append(f"{tid}: certify_reconciliation requires evidence.unresolved_breaks")
            elif not isinstance(ub, int) or isinstance(ub, bool):
                errors.append(f"{tid}: evidence.unresolved_breaks must be an integer")
            elif ub != 0:
                errors.append(f"{tid}: {ub} unresolved reconciliation break(s) — clear via gl-reconciler "
                              f"before certifying (fail closed)")

        for dep in t.get("depends_on") or []:
            if dep not in ids:
                errors.append(f"{tid}: depends_on references unknown task {dep!r}")
            if dep == tid:
                errors.append(f"{tid}: task cannot depend on itself")

    cycle = _has_cycle(ids)
    if cycle:
        errors.append(f"dependency cycle detected: {' -> '.join(cycle)} -> {cycle[0]}")

    if not doc.get("catalog_version"):
        warnings.append("no catalog_version — record the versioned close-action catalog used for reproducibility")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "close_run_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    errors, warnings = validate(doc)
    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"input validation: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
