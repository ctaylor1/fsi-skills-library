#!/usr/bin/env python3
"""Deterministic input validation for transaction-process-tracker.

Validates a deal-process intake bundle before the tracker is assembled. Fails closed on
structural problems; warns on data gaps and control conditions that will surface as
reminders or open items (undated milestones, missing prior snapshot, control-gate breaches,
recorded approvals with no source reference).

Input schema (JSON): see references/source-map.md and references/domain-rules.md. Key fields:
  config_version, process_id, deal_name, as_of_date, reminder_lookahead_days,
  stage_order[], required_approvals[],
  parties[{party_id, name, type, engagement, stage, nda_status, access_status,
           bid{type, amount, currency, received_date, source_ref},
           milestones[{milestone_id, label, due_date, status, source_ref}], source_ref}],
  approvals[{approval_id, type, approver_role, approver, status, date, source_ref}],
  prior_snapshot{as_of_date, parties{party_id: {stage, nda_status, access_status}}}

Usage: python validate_input.py intake.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from datetime import date
from pathlib import Path

REQUIRED_TOP = ("config_version", "process_id", "as_of_date", "parties")
REQUIRED_PARTY = ("party_id", "name", "source_ref")
DEFAULT_STAGE_ORDER = ["outreach", "nda", "access", "diligence", "bid", "approval"]
DONE_MILESTONE = {"complete", "completed", "done", "received", "executed", "satisfied", "closed"}


def _parse_date(s):
    try:
        return date.fromisoformat(str(s))
    except Exception:
        return None


def _stage_index(stage, order):
    return order.index(stage) if stage in order else -1


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc or doc[k] in (None, ""):
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if _parse_date(doc.get("as_of_date")) is None:
        errors.append(f"as_of_date is not an ISO date: {doc.get('as_of_date')!r}")

    order = doc.get("stage_order") or DEFAULT_STAGE_ORDER
    if not isinstance(order, list) or not order:
        errors.append("stage_order must be a non-empty list when provided")
        order = DEFAULT_STAGE_ORDER

    parties = doc.get("parties")
    if not isinstance(parties, list) or not parties:
        errors.append("parties must be a non-empty list")
        return errors, warnings

    access_i = _stage_index("access", order)
    diligence_i = _stage_index("diligence", order)

    ids = set()
    for i, p in enumerate(parties):
        tag = f"parties[{i}] ({p.get('party_id','?')})"
        for k in REQUIRED_PARTY:
            if k not in p or p[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        pid = p.get("party_id")
        if pid in ids:
            errors.append(f"{tag}: duplicate party_id")
        ids.add(pid)

        stage = p.get("stage")
        if stage is not None and stage not in order:
            warnings.append(f"{tag}: stage {stage!r} not in stage_order -> not gated/counted by stage")
        engagement = p.get("engagement", "active")
        nda = p.get("nda_status", "none")
        access = p.get("access_status", "none")
        si = _stage_index(stage, order)

        # control-gate warnings (assembler surfaces these as control-exception open items)
        if engagement == "active":
            if access == "granted" and nda != "executed":
                warnings.append(f"{tag}: data-room access granted without an executed NDA -> control exception")
            if access_i >= 0 and si >= access_i and nda != "executed":
                warnings.append(f"{tag}: at stage {stage!r} (>= access) without an executed NDA -> control exception")
            if diligence_i >= 0 and si >= diligence_i and access != "granted":
                warnings.append(f"{tag}: at stage {stage!r} (>= diligence) without granted access -> control exception")

        for j, m in enumerate(p.get("milestones") or []):
            mtag = f"{tag} milestone[{j}] ({m.get('milestone_id','?')})"
            if not m.get("milestone_id") or not m.get("source_ref"):
                errors.append(f"{mtag}: requires 'milestone_id' and 'source_ref'")
            status = str(m.get("status", "")).lower()
            if status not in DONE_MILESTONE and _parse_date(m.get("due_date")) is None:
                warnings.append(f"{mtag}: open milestone has no valid due_date -> reminder cannot be computed")

        bid = p.get("bid")
        if isinstance(bid, dict) and not bid.get("source_ref"):
            errors.append(f"{tag}: bid recorded without a 'source_ref' (uncited)")

    for i, a in enumerate(doc.get("approvals") or []):
        if not a.get("type") or not a.get("status"):
            errors.append(f"approvals[{i}]: requires 'type' and 'status'")
        if a.get("status") == "recorded" and not a.get("source_ref"):
            errors.append(f"approvals[{i}] ({a.get('type','?')}): recorded approval missing 'source_ref'")

    if not doc.get("required_approvals"):
        warnings.append("no required_approvals configured -> approval capture limited")
    if not doc.get("prior_snapshot"):
        warnings.append("no prior_snapshot provided -> change log will be limited (all parties shown as added)")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "tracker_intake_example.json"
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
    print(f"input validation: {len(warnings)} warning(s), {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
