#!/usr/bin/env python3
"""Deterministic assembly of the incident coordination pack for
cyber-incident-response-coordinator.

Reads an incident-record file (see validate_input.py), normalizes and orders the chronology,
computes role coverage, task status (open/overdue by phase), evidence chain-of-custody
completeness, decision status (pending vs human-adjudicated), a SUGGESTED severity band, and
deterministic NOTIFICATION REMINDERS that route obligations to humans. It emits a
machine-readable coordination pack the SKILL wraps in a plain-language brief.

IMPORTANT: This produces a coordination record with recommendations and evidence ONLY. It
never makes a regulated decision, sets a binding severity, closes the incident, files a
regulatory notification, or writes a system of record. Every decision remains pending human
adjudication (a decision may be recorded as adjudicated ONLY when a human decided_by is
present in the input). The severity band and notification reminders are deterministic and
documented in references/domain-rules.md.

Usage:
  python calculate_or_transform.py incident.json | --selftest
Prints the coordination JSON to stdout.
"""
from __future__ import annotations
import json, sys
from datetime import datetime
from pathlib import Path

DEFAULT_CONFIG = {
    "major_breach_records": 500,
    "overdue_grace_minutes": 0,
    "mandatory_roles": ["incident_commander", "scribe", "technical_lead", "comms_lead", "legal_liaison"],
}
DISCLAIMER = ("Coordination record only; recommendations and evidence for human adjudication. "
              "No regulated decision, severity classification, incident closure, regulatory "
              "filing, or system-of-record write has been performed by this skill.")
TERMINAL_DECISION = {"adjudicated", "approved", "rejected"}


def _parse_dt(s: str) -> datetime:
    s = str(s)
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return datetime.strptime(s[:10], "%Y-%m-%d")


def suggest_severity(impact: dict, cfg: dict) -> tuple[str, list[str]]:
    """Deterministic SUGGESTED severity band + basis. Never a binding classification."""
    reasons: list[str] = []
    tol = bool(impact.get("impact_tolerance_breached"))
    scope = impact.get("scope")
    exposure = bool(impact.get("confirmed_data_exposure"))
    regulated = bool(impact.get("regulated_data"))
    records = impact.get("records_exposed") or 0
    try:
        records = int(records)
    except (TypeError, ValueError):
        records = 0
    crit = bool(impact.get("critical_service_affected"))
    major = int(cfg.get("major_breach_records", 500))

    if tol:
        reasons.append("impact tolerance breached")
    if scope == "enterprise":
        reasons.append("enterprise-wide scope")
    if exposure and regulated and records >= major:
        reasons.append(f"confirmed regulated-data exposure of {records} records (>= {major})")
    if reasons:
        return "SEV1", reasons

    if crit:
        reasons.append("critical service affected")
    if exposure:
        reasons.append("confirmed data exposure")
    if scope == "multi-system":
        reasons.append("multi-system scope")
    if reasons:
        return "SEV2", reasons

    if records > 0:
        reasons.append(f"{records} records potentially exposed")
    if impact.get("suspected_compromise"):
        reasons.append("suspected compromise, contained scope")
    if scope == "single-system":
        reasons.append("single-system scope")
    if reasons:
        return "SEV3", reasons

    return "SEV4", ["no material impact flags set"]


def notification_reminders(impact: dict) -> list[dict]:
    """Deterministic REMINDERS routed to humans. Not determinations that filing is required
    and never a filing. Each names the human/adjacent-skill owner of the actual decision."""
    out = []
    if impact.get("confirmed_data_exposure") and impact.get("regulated_data"):
        out.append({
            "trigger": "confirmed regulated/customer-data exposure",
            "reminder": "Data-protection and breach-notification clocks MAY apply. Route the "
                        "notification decision to legal/privacy counsel; for drafting jurisdiction "
                        "reports, hand off to operational-resilience-reporter.",
            "route_to": ["legal/privacy counsel (human)", "operational-resilience-reporter"],
            "note": "Reminder only — not a determination that notification is required and not a filing."})
    if impact.get("impact_tolerance_breached"):
        out.append({
            "trigger": "impact tolerance breached on a critical service",
            "reminder": "Operational-resilience regulatory reporting MAY apply. Route to the "
                        "resilience/legal owners; hand off report drafting to operational-resilience-reporter.",
            "route_to": ["operational resilience owner (human)", "operational-resilience-reporter"],
            "note": "Reminder only — not a determination and not a filing."})
    if impact.get("critical_service_affected"):
        out.append({
            "trigger": "critical service affected",
            "reminder": "BCP/continuity obligations and customer/stakeholder communications MAY apply. "
                        "Confirm with the business-continuity and communications owners.",
            "route_to": ["business-continuity owner (human)", "comms lead (human)"],
            "note": "Reminder only — no communication has been sent by this skill."})
    return out


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    as_of = _parse_dt(doc["as_of"])
    impact = doc.get("impact") or {}

    # chronology: normalize + order
    chron = sorted((doc.get("chronology") or []), key=lambda e: str(e.get("ts", "")))
    chronology = [{"ts": e.get("ts"), "actor": e.get("actor"), "entry_type": e.get("entry_type"),
                   "description": e.get("description"), "source_ref": e.get("source_ref")}
                  for e in chron]

    # roles
    mandatory = cfg.get("mandatory_roles") or DEFAULT_CONFIG["mandatory_roles"]
    filled_map = {r.get("role"): r.get("assignee") for r in (doc.get("roles") or []) if r.get("assignee")}
    roles = {"filled": [{"role": r, "assignee": filled_map[r]} for r in filled_map],
             "missing": [r for r in mandatory if r not in filled_map]}

    # tasks
    tasks = doc.get("tasks") or []
    open_tasks, overdue, by_phase = [], [], {}
    done = 0
    for t in tasks:
        by_phase.setdefault(t.get("phase", "unspecified"), {"open": 0, "done": 0})
        st = t.get("status")
        if st == "done":
            done += 1
            by_phase[t.get("phase", "unspecified")]["done"] += 1
            continue
        by_phase[t.get("phase", "unspecified")]["open"] += 1
        row = {"task_id": t.get("task_id"), "phase": t.get("phase"),
               "description": t.get("description"), "owner": t.get("owner"),
               "status": st, "due": t.get("due")}
        open_tasks.append(row)
        due = t.get("due")
        if due and _parse_dt(due) < as_of:
            overdue.append(row)

    # evidence chain-of-custody completeness
    evidence = []
    for ev in (doc.get("evidence") or []):
        complete = bool(ev.get("source_ref")) and bool(ev.get("hash")) and bool(ev.get("custody"))
        evidence.append({"evidence_id": ev.get("evidence_id"), "type": ev.get("type"),
                         "description": ev.get("description"), "source_ref": ev.get("source_ref"),
                         "hash": ev.get("hash"), "custody": ev.get("custody"),
                         "custody_complete": complete})

    # decisions: preserve human adjudication, flag pending
    decisions = []
    for d in (doc.get("decisions") or []):
        st = d.get("status", "pending")
        decisions.append({
            "decision_id": d.get("decision_id"), "description": d.get("description"),
            "recommendation": d.get("recommendation"), "adjudicator": d.get("adjudicator"),
            "status": st, "decided_by": d.get("decided_by"),
            "awaiting_human": st not in TERMINAL_DECISION or not d.get("decided_by")})

    severity, basis = suggest_severity(impact, cfg)
    reminders = notification_reminders(impact)

    post_actions = doc.get("post_incident_actions") or []

    return {
        "coordination_id": f"circ-{doc['incident_id']}-{str(doc['as_of'])[:10]}-0001",
        "incident_id": doc["incident_id"],
        "as_of": doc["as_of"],
        "config_version": doc.get("config_version"),
        "severity_config": {"major_breach_records": int(cfg.get("major_breach_records", 500))},
        "impact": impact,
        "severity_suggested": severity,
        "severity_basis": basis,
        "roles": roles,
        "chronology": chronology,
        "tasks": {"open": open_tasks, "overdue": overdue, "done_count": done, "by_phase": by_phase},
        "evidence": evidence,
        "decisions": decisions,
        "communications": doc.get("communications") or [],
        "dependencies": doc.get("dependencies") or [],
        "notification_reminders": reminders,
        "post_incident_actions": post_actions,
        "record_status": "open",
        "readiness": {
            "roles_missing": len(roles["missing"]),
            "open_tasks": len(open_tasks),
            "overdue_tasks": len(overdue),
            "decisions_awaiting_human": sum(1 for d in decisions if d["awaiting_human"]),
            "evidence_custody_incomplete": sum(1 for e in evidence if not e["custody_complete"]),
        },
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "incident_record.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
