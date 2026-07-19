#!/usr/bin/env python3
"""Deterministic input validation for cyber-incident-response-coordinator.

Validates an incident-record file before the coordination pack is assembled. Fails closed on
structural problems (missing case identity, malformed sections); warns on evidence-quality and
coordination gaps (unfilled mandatory roles, chronology entries without a source, decisions
without a human adjudicator) that a reviewer must weigh but that do not block coordination.

Input schema (JSON): see references/source-map.md and references/domain-rules.md. Key fields:
  incident_id, as_of (YYYY-MM-DD[THH:MM:SS]), config_version, declared_by,
  classification_status, config{major_breach_records, mandatory_roles[]},
  impact{critical_service_affected, impact_tolerance_breached, confirmed_data_exposure,
         regulated_data, records_exposed, scope, suspected_compromise},
  roles[{role, assignee}], chronology[{ts, entry_type, description, source_ref}],
  tasks[{task_id, phase, description, owner, status, due}],
  evidence[{evidence_id, description, source_ref, hash, custody}],
  decisions[{decision_id, description, adjudicator, status, decided_by}],
  communications[...], dependencies[...], post_incident_actions[...]

Usage:
  python validate_input.py incident.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("incident_id", "as_of", "config_version", "declared_by",
                "impact", "roles", "chronology", "tasks", "evidence", "decisions")
DEFAULT_ROLES = ("incident_commander", "scribe", "technical_lead", "comms_lead", "legal_liaison")
TASK_STATUS = {"open", "in-progress", "blocked", "done"}
DECISION_STATUS = {"pending", "adjudicated", "approved", "deferred", "rejected"}
TERMINAL_DECISION = {"adjudicated", "approved", "rejected"}


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")

    if str(doc.get("classification_status", "proposed")) not in ("proposed", "under-review"):
        warnings.append("classification_status is not 'proposed'/'under-review' — severity is a "
                        "human-adjudicated call; this skill only proposes a band")

    impact = doc.get("impact")
    if not isinstance(impact, dict):
        errors.append("impact must be an object")
    else:
        if "scope" in impact and impact["scope"] not in ("single-system", "multi-system", "enterprise"):
            warnings.append(f"impact.scope {impact['scope']!r} unrecognized — severity basis may be incomplete")
        if impact.get("confirmed_data_exposure") and impact.get("records_exposed") in (None, ""):
            warnings.append("confirmed_data_exposure set but records_exposed missing — breach-scale basis is incomplete")

    cfg = doc.get("config") or {}
    mandatory = cfg.get("mandatory_roles") or list(DEFAULT_ROLES)
    filled = {r.get("role") for r in (doc.get("roles") or []) if r.get("assignee")}
    for r in mandatory:
        if r not in filled:
            warnings.append(f"mandatory IR role unfilled: {r} — coordination gap for reviewer")

    chron = doc.get("chronology") or []
    if not isinstance(chron, list) or not chron:
        errors.append("chronology must be a non-empty list")
    else:
        for i, e in enumerate(chron):
            tag = f"chronology[{i}]"
            for k in ("ts", "entry_type", "description"):
                if not e.get(k):
                    errors.append(f"{tag}: missing '{k}'")
            if not e.get("source_ref"):
                warnings.append(f"{tag}: no source_ref — this timeline entry will not be citable in the pack")

    seen_task = set()
    for i, t in enumerate(doc.get("tasks") or []):
        tag = f"tasks[{i}] ({t.get('task_id','?')})"
        for k in ("task_id", "phase", "description", "status"):
            if not t.get(k):
                errors.append(f"{tag}: missing '{k}'")
        if t.get("status") and t["status"] not in TASK_STATUS:
            errors.append(f"{tag}: status must be one of {sorted(TASK_STATUS)}")
        if t.get("task_id") in seen_task:
            errors.append(f"{tag}: duplicate task_id")
        seen_task.add(t.get("task_id"))
        if not t.get("owner"):
            warnings.append(f"{tag}: no owner — unassigned action")

    for i, ev in enumerate(doc.get("evidence") or []):
        tag = f"evidence[{i}] ({ev.get('evidence_id','?')})"
        for k in ("evidence_id", "description"):
            if not ev.get(k):
                errors.append(f"{tag}: missing '{k}'")
        if not ev.get("source_ref"):
            warnings.append(f"{tag}: no source_ref — evidence not citable")
        if not ev.get("hash") or not ev.get("custody"):
            warnings.append(f"{tag}: missing hash/custody — chain-of-custody incomplete")

    seen_dec = set()
    for i, d in enumerate(doc.get("decisions") or []):
        tag = f"decisions[{i}] ({d.get('decision_id','?')})"
        for k in ("decision_id", "description"):
            if not d.get(k):
                errors.append(f"{tag}: missing '{k}'")
        st = d.get("status")
        if st and st not in DECISION_STATUS:
            errors.append(f"{tag}: status must be one of {sorted(DECISION_STATUS)}")
        if d.get("decision_id") in seen_dec:
            errors.append(f"{tag}: duplicate decision_id")
        seen_dec.add(d.get("decision_id"))
        if not d.get("adjudicator"):
            warnings.append(f"{tag}: no adjudicator named — every decision must route to a human owner")
        if st in TERMINAL_DECISION and not d.get("decided_by"):
            warnings.append(f"{tag}: status {st!r} but no decided_by — a terminal decision needs a human decider")

    if not doc.get("communications"):
        warnings.append("no communications recorded — confirm stakeholder updates are being logged")
    if not doc.get("dependencies"):
        warnings.append("no dependencies recorded — impact/impact-tolerance basis may be incomplete")

    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "incident_record.json"
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
