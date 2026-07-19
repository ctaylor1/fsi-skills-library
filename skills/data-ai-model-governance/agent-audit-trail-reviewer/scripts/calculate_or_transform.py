#!/usr/bin/env python3
"""Deterministic control-review engine for agent-audit-trail-reviewer.

Reads an agent-run audit trail (see validate_input.py), evaluates a fixed set of
reproducibility and control-effectiveness checks, and emits findings with cited evidence,
a deterministic severity per finding, and a triage disposition band.

IMPORTANT (R3 decision-support): this produces *findings, evidence, and a triage
suggestion* only. It never attests control effectiveness, closes/files a finding, or writes
a system of record. Every finding requires human adjudication. The severity and disposition
mappings are deterministic and documented in references/domain-rules.md so a review is
reproducible.

Usage:
  python calculate_or_transform.py trail.json | --selftest
Prints the review JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

DISCLAIMER = ("Control-review evidence only; not a control attestation or adjudication. No "
              "finding has been closed, filed, or written to a system of record; human "
              "adjudication is required.")

# Deterministic severity by finding type (see references/domain-rules.md).
TYPE_SEVERITY = {
    "prohibited_autonomous_action": "high",
    "unauthorized_override": "high",
    "self_approval": "high",
    "missing_approval": "medium",
    "after_the_fact_approval": "medium",
    "out_of_scope_tool": "medium",
    "retention_gap": "medium",
    "evidence_traceability_gap": "low",
    "reproducibility_gap": "low",
    "logging_gap": "low",
}
DEFAULT_REPRO_FIELDS = ["model_id", "model_version", "prompt_version", "config_version"]


def _cite(run_id: str, event_id: str, ts: str) -> str:
    return f"trail:run={run_id};event={event_id}@{ts}"


def _ev(run_id: str, e: dict, ref: str = "") -> dict:
    return {"event_id": e.get("event_id"), "ref": ref or e.get("ref") or e.get("source_ref") or e.get("tool"),
            "citation": _cite(run_id, e.get("event_id"), e.get("ts"))}


def compute(doc: dict) -> dict:
    run_id = doc["run_id"]
    run = doc.get("run") or {}
    cfg = doc.get("config") or {}
    events = doc.get("events") or []
    allowed_tools = set(cfg.get("allowed_tools") or [])
    approval_classes = set(cfg.get("approval_required_action_classes") or ["write", "decision"])
    required_retained = list(cfg.get("required_retained_objects") or [])
    req_repro = list(cfg.get("required_repro_fields") or DEFAULT_REPRO_FIELDS)

    findings: list[dict] = []
    seq = [0]

    def add(ftype: str, domain: str, description: str, evidence: list, recommendation: str):
        seq[0] += 1
        findings.append({
            "finding_id": f"F-{seq[0]:03d}",
            "type": ftype,
            "control_domain": domain,
            "severity": TYPE_SEVERITY[ftype],
            "description": description,
            "evidence": evidence,
            "recommendation": recommendation,
        })

    # ---- Reproducibility ----
    present = [f for f in req_repro if run.get(f) not in (None, "")]
    missing = [f for f in req_repro if run.get(f) in (None, "")]
    if missing:
        add("reproducibility_gap", "reproducibility",
            f"Run header is missing reproducibility field(s) {missing}; the run cannot be "
            f"deterministically reproduced from the recorded trail.",
            [{"event_id": "run-header", "ref": f"run={run_id}",
              "citation": f"trail:run={run_id}#header@{doc.get('as_of')}"}],
            "Route to the model/agent owner to backfill the missing reproducibility fields in the run record.")

    # ---- Per-event control checks ----
    approvals_by_target: dict = {}
    for e in events:
        if e.get("type") == "approval" and e.get("for_event"):
            approvals_by_target.setdefault(e["for_event"], []).append(e)

    for e in events:
        et = e.get("type")
        if et == "retrieval":
            if not str(e.get("citation") or "").strip():
                add("evidence_traceability_gap", "traceability",
                    f"Retrieval event {e.get('event_id')} has no citation to its source; the "
                    f"retrieved material cannot be traced to an authoritative record.",
                    [_ev(run_id, e)],
                    "Route to the agent owner to confirm the retrieved source and record its citation.")
        elif et == "tool_call":
            tool = e.get("tool")
            aclass = e.get("action_class")
            gated = bool(e.get("approval_required")) or aclass in approval_classes
            appr = approvals_by_target.get(e.get("event_id"), [])
            approved = [a for a in appr if str(a.get("decision", "")).lower() == "approved"]
            # out-of-scope tool
            if allowed_tools and tool not in allowed_tools:
                add("out_of_scope_tool", "least-privilege",
                    f"Tool {tool!r} (event {e.get('event_id')}) is not in the run's allowed-tool "
                    f"set; the call falls outside the approved least-privilege scope.",
                    [_ev(run_id, e, ref=f"tool={tool}")],
                    "Route to an agent-permission review to confirm whether the tool should be in scope.")
            # gated action without valid approval
            if gated and not approved:
                if aclass == "decision":
                    add("prohibited_autonomous_action", "human-oversight",
                        f"Tool {tool!r} executed a regulated decision ({e.get('operation')}) at "
                        f"event {e.get('event_id')} with no recorded human approval event; a "
                        f"regulated decision was taken without the required oversight gate.",
                        [_ev(run_id, e, ref=f"tool={tool};op={e.get('operation')}")],
                        "Escalate to a human adjudicator; a regulated decision must have a human approval gate.")
                else:
                    add("missing_approval", "human-oversight",
                        f"Tool {tool!r} performed a {aclass} operation ({e.get('operation')}) at "
                        f"event {e.get('event_id')} that required approval, but no matching approval "
                        f"event is recorded.",
                        [_ev(run_id, e, ref=f"tool={tool};op={e.get('operation')}")],
                        "Route to the control owner to confirm whether the required approval occurred out-of-band.")
            # after-the-fact approval (approval timestamp later than the action)
            for a in appr:
                if str(a.get("ts", "")) > str(e.get("ts", "")):
                    add("after_the_fact_approval", "human-oversight",
                        f"Approval {a.get('event_id')} for {tool!r} (event {e.get('event_id')}) is "
                        f"timestamped after the action executed; the control did not operate as a "
                        f"pre-execution gate.",
                        [_ev(run_id, a, ref=f"approves={e.get('event_id')}")],
                        "Route to the control owner to confirm the sequencing of approval versus execution.")
            # self-approval (approver is the agent/actor itself)
            for a in appr:
                if str(a.get("approver", "")).lower() in ("agent", str(doc.get("agent_id", "")).lower()):
                    add("self_approval", "segregation-of-duties",
                        f"Approval {a.get('event_id')} for event {e.get('event_id')} was granted by "
                        f"the agent itself; there is no independent human approver.",
                        [_ev(run_id, a, ref="approver=agent")],
                        "Escalate; a gated action requires an independent human approver, not self-approval.")
        elif et == "override":
            if str(e.get("actor", "")).lower() != "human":
                add("unauthorized_override", "human-oversight",
                    f"Override {e.get('event_id')} of a {e.get('overrode')} was performed by a "
                    f"non-human actor ({e.get('actor')}); a control was bypassed without human authority.",
                    [_ev(run_id, e, ref=f"overrode={e.get('overrode')}")],
                    "Escalate to a human adjudicator; a guardrail/approval override requires recorded human authority.")

    # ---- Retention ----
    retained = {str(e.get("object")) for e in events
                if e.get("type") == "retention" and e.get("retained")}
    for obj in required_retained:
        if obj not in retained:
            add("retention_gap", "records-retention",
                f"Required object {obj!r} has no retention record marking it retained; the trail "
                f"does not evidence that {obj} artifacts were preserved per policy.",
                [{"event_id": "retention", "ref": f"object={obj}",
                  "citation": f"trail:run={run_id}#retention={obj}@{doc.get('as_of')}"}],
                "Route to records management to confirm the object is retained under the required class.")

    # ---- Logging integrity (event ordering / uniqueness in given order) ----
    seen: set = set()
    dup = False
    for e in events:
        if e.get("event_id") in seen:
            dup = True
        seen.add(e.get("event_id"))
    ts_seq = [str(e.get("ts")) for e in events]
    out_of_order = any(ts_seq[i] > ts_seq[i + 1] for i in range(len(ts_seq) - 1))
    if dup or out_of_order:
        why = []
        if dup:
            why.append("duplicate event_id(s)")
        if out_of_order:
            why.append("events not in non-decreasing timestamp order")
        add("logging_gap", "logging-integrity",
            f"Audit-log integrity issue: {', '.join(why)}; the trail's ordering/uniqueness "
            f"cannot be relied on as a faithful record.",
            [{"event_id": "log", "ref": f"run={run_id}",
              "citation": f"trail:run={run_id}#log@{doc.get('as_of')}"}],
            "Route to the platform/observability owner to verify log capture integrity.")

    counts = {"high": 0, "medium": 0, "low": 0}
    for f in findings:
        counts[f["severity"]] += 1
    disposition = _disposition(counts)

    return {
        "review_id": f"aatr-{run_id}-{doc['as_of']}-0001",
        "run_id": run_id,
        "agent_id": doc.get("agent_id"),
        "as_of": doc["as_of"],
        "policy_version": doc.get("policy_version"),
        "reproducibility": {"complete": not missing, "present_fields": present, "missing_fields": missing},
        "findings": findings,
        "finding_counts": counts,
        "disposition": disposition,
        "human_adjudication_required": True,
        "disclaimer": DISCLAIMER,
    }


def _disposition(counts: dict) -> str:
    if counts.get("high", 0) >= 1 or counts.get("medium", 0) >= 3:
        return "Escalate"
    if sum(counts.values()) >= 1:
        return "Review"
    return "No exceptions noted"


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "trail_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
