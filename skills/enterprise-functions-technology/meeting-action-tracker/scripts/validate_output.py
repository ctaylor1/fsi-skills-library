#!/usr/bin/env python3
"""Deterministic output validation for meeting-action-tracker.

Enforces the R1 "Draft & package" guardrails before an action package is handed to a human for
review, confirmation, and (human-performed) delivery:
  1. Traceability: every register/decision/open item is cited (no unsupported assertion); an
     item with no citation may only carry status `unsupported`.
  2. Ready-discipline: a `ready` action is owner-resolved, owner-confirmed, date-confirmed, and
     dependency-clean; a `ready` decision names a cited decision-maker.
  3. Committed sets (`action_register`/`decision_log`/`open_questions`) contain only `ready` items.
  4. Draft comms: every message is `delivery: draft` with `approval_required: true` and cited.
  5. No silent system-change language (created/assigned/sent/scheduled/updated a tracker).
  6. No personalized investment/legal/tax advice.
  7. The standing disclaimer (draft-only; no send; no write; confirm before committed) is present.

Fails closed on any miss so a defective or overreaching package cannot be presented as ready.

Usage: python validate_output.py package.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ALLOWED_STATUSES = {"ready", "needs-confirmation", "blocked", "unsupported", "possible-duplicate"}
STANDING_NOTE = (
    "Draft meeting outputs for human review only; this skill does not create tasks, send "
    "messages, or change any tracker, calendar, or system of record, and every action, owner, "
    "and due date must be confirmed before it is treated as committed."
)
SYSTEM_CHANGE_PATTERNS = [
    r"\bi (have )?(created|opened|logged) the (task|ticket|issue|card)\b",
    r"\b(created|added|logged) .{0,30} in (jira|asana|linear|monday|trello|clickup)\b",
    r"\bsent the (reminder|email|message|update|recap|invite)\b",
    r"\b(i|we) (have )?sent (the|it|them|out)\b",
    r"\bposted (it |them |the .{0,20})?to (slack|teams)\b",
    r"\bscheduled the (meeting|invite|follow-?up|calendar)\b",
    r"\bupdated the (tracker|board|ticket|task)\b",
    r"\bassigned .{0,30} in (jira|asana|linear|monday|trello|clickup)\b",
    r"\bmarked .{0,20}(complete|completed|done|closed)\b",
    r"\bclosed the (ticket|task|issue)\b",
]
ADVICE_PATTERNS = [
    r"\b(investment|legal|tax) advice\b",
    r"\bas your (attorney|lawyer|financial advisor|accountant)\b",
    r"\byou should (buy|sell|invest in)\b",
]


def _committed_ok(doc, items_by_id, errors, kind, key):
    for entry in doc.get(key) or []:
        iid = entry.get("item_id")
        it = items_by_id.get(iid)
        if it is None:
            errors.append(f"{key}: entry {iid!r} has no matching item record")
            continue
        if it.get("status") != "ready":
            errors.append(f"{key}: {iid} is in the committed set but status is {it.get('status')!r} (only 'ready' allowed)")
        if not entry.get("citations"):
            errors.append(f"{key}: {iid} is committed without a citation (unsupported assertion)")


def validate(doc: dict) -> list[str]:
    errors: list[str] = []
    items = doc.get("items") or []
    if not items:
        return ["package output has no items"]

    items_by_id = {}
    for it in items:
        iid = it.get("item_id", "?")
        items_by_id[iid] = it
        status = it.get("status")
        if status not in ALLOWED_STATUSES:
            errors.append(f"{iid}: disallowed status {status!r} (created/assigned/sent/closed not permitted)")
        cited = bool(it.get("citations"))
        if not cited and status != "unsupported":
            errors.append(f"{iid}: no citation but status {status!r} (an unsupported assertion may only be 'unsupported')")
        if status == "ready":
            if not cited:
                errors.append(f"{iid}: ready item is not cited")
            if it.get("type") == "action":
                if it.get("owner_status") != "resolved":
                    errors.append(f"{iid}: ready action has unresolved owner ({it.get('owner_status')!r})")
                if not it.get("owner_confirmed"):
                    errors.append(f"{iid}: ready action is not owner-confirmed")
                if not it.get("due_confirmed"):
                    errors.append(f"{iid}: ready action has an unconfirmed due date")
                if it.get("dependency_status") not in (None, "ok"):
                    errors.append(f"{iid}: ready action has dependency issue {it.get('dependency_status')!r}")
            if it.get("type") == "decision" and not it.get("decided_by"):
                errors.append(f"{iid}: ready decision has no cited decision-maker")

    _committed_ok(doc, items_by_id, errors, "action", "action_register")
    _committed_ok(doc, items_by_id, errors, "decision", "decision_log")
    _committed_ok(doc, items_by_id, errors, "open", "open_questions")

    for c in doc.get("draft_comms") or []:
        label = c.get("type", "?")
        if c.get("delivery") != "draft":
            errors.append(f"draft_comms[{label}]: delivery is {c.get('delivery')!r}, must be 'draft' (this skill never sends)")
        if c.get("approval_required") is not True:
            errors.append(f"draft_comms[{label}]: approval_required must be true")
        if not c.get("citations"):
            errors.append(f"draft_comms[{label}]: message has no citations")

    scan = json.dumps(items) + " " + json.dumps(doc.get("draft_comms") or []) + " " + str(doc.get("narrative", ""))
    for pat in SYSTEM_CHANGE_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"prohibited system-change language detected: {m.group(0)!r} (this skill never sends/creates/updates)")
    for pat in ADVICE_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"prohibited advice language detected: {m.group(0)!r}")

    if STANDING_NOTE.lower() not in str(doc.get("standing_note", "")).lower():
        errors.append("missing standing note")
    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "register_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    errors = validate(doc)
    for e in errors:
        print("ERROR", e)
    print(f"output validation: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
