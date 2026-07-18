#!/usr/bin/env python3
"""Deterministic prompt/agent risk-review computation for prompt-and-agent-risk-reviewer.

Reads an agent review package (see validate_input.py), evaluates each control in the
versioned control catalog against the declared configuration, attaches evidence + citations
to every fired finding, and maps the fired-finding severities to a recommended risk rating
and a recommended disposition. Emits a machine-readable core the SKILL wraps in a
plain-language review.

IMPORTANT: This produces explainable *findings and a recommendation for a human adjudicator*
only. It NEVER approves an agent for deployment, grants a risk acceptance or exception,
attests a control, or closes the review. The rating/disposition mapping is deterministic and
documented in references/domain-rules.md. Missing/undocumented control blocks are treated as
controls-not-evidenced (the risk-flagging default) and surfaced in data_gaps.

Usage:
  python calculate_or_transform.py agent_review.json | --selftest
Prints the review JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

HIGH_IMPACT = {"write", "external", "payment", "irreversible"}
SENSITIVE_CLASS = {"Confidential", "Restricted", "PII"}
SEV_RANK = {"Low": 1, "Moderate": 2, "High": 3, "Critical": 4}
RANK_SEV = {v: k for k, v in SEV_RANK.items()}
OPTIONAL_BLOCKS = ("memory", "retrieval", "guardrails", "failure_mode", "observability")

DISCLAIMER = ("Risk review evidence and recommendations only; not an approval, risk "
              "acceptance, or attestation. Deployment requires human adjudication by the "
              "accountable AI risk owner.")
ADJUDICATION_NOTE = ("Recommendation only; requires human adjudication before any deployment "
                     "decision. No approval, risk acceptance, attestation, or review closure "
                     "has been recorded.")


def _cite(agent_id: str, as_of: str, locus: str) -> str:
    return f"agentspec:{agent_id}#{locus}@{as_of}"


def compute(doc: dict) -> dict:
    agent = doc.get("agent") or {}
    agent_id = doc.get("agent_id", "?")
    as_of = doc.get("as_of", "?")

    tools = agent.get("tools") or []
    mem = agent.get("memory") or {}
    retr = agent.get("retrieval") or {}
    grd = agent.get("guardrails") or {}
    fail = agent.get("failure_mode") or {}
    obs = agent.get("observability") or {}
    surfaces = agent.get("untrusted_input_surfaces") or []
    prohibited = agent.get("prohibited_surface") or []
    autonomy = agent.get("autonomy")
    dclass = agent.get("data_classification")

    def cite(locus):
        return _cite(agent_id, as_of, locus)

    def ev(locus, detail):
        return {"locus": locus, "detail": detail, "citation": cite(locus)}

    high_impact_tools = [t for t in tools if t.get("effect") in HIGH_IMPACT]
    untrusted_sources = [s for s in (retr.get("sources") or []) if s.get("trust") == "untrusted"]
    has_untrusted = bool(surfaces) or bool(untrusted_sources) or bool(mem.get("persists_untrusted"))

    findings = []

    def add(cid, title, severity, fired, rationale, evidence, remediation):
        findings.append({
            "control_id": cid, "title": title, "severity": severity, "fired": bool(fired),
            "rationale": rationale, "evidence": evidence if fired else [],
            "remediation": remediation,
        })

    def tool_ev(ts):
        return [ev(f"tools[{t.get('name','?')}]", f"effect={t.get('effect')}") for t in ts]

    # C-INJ-01 (Critical) untrusted input can reach a high-impact tool without injection mediation
    inj01 = has_untrusted and bool(high_impact_tools) and not grd.get("injection_mediation")
    add("C-INJ-01", "Untrusted-input to privileged-action path", "Critical", inj01,
        "Untrusted input surfaces can reach high-impact tools with no injection-mediation guardrail.",
        ([ev("untrusted_input_surfaces", ", ".join(surfaces))] if surfaces else [])
        + ([ev("retrieval.sources", "untrusted retrieval source present")] if untrusted_sources else [])
        + tool_ev(high_impact_tools)
        + [ev("guardrails.injection_mediation", "absent/false")],
        "Add an injection-mediation guardrail, or require human approval on every high-impact tool "
        "reachable from an untrusted surface, or isolate untrusted input from privileged actions.")

    # C-INJ-02 (High) untrusted content persisted in memory then re-fed to the prompt with high-impact tools
    inj02 = bool(mem.get("persists_untrusted")) and bool(mem.get("feeds_prompt")) and bool(high_impact_tools)
    add("C-INJ-02", "Injection-persistent memory", "High", inj02,
        "Untrusted content persists in memory and is re-fed to the prompt while high-impact tools are enabled.",
        [ev("memory", "persists_untrusted and feeds_prompt")] + tool_ev(high_impact_tools),
        "Do not persist untrusted content into prompt-feeding memory, or sanitize/quarantine it before reuse.")

    # C-TOOL-01 (High) autonomous high-impact tool without a human-approval gate
    offending = [t for t in high_impact_tools if autonomy == "autonomous" and not t.get("human_approval")]
    add("C-TOOL-01", "Autonomous high-impact tool without human approval", "High", bool(offending),
        "An autonomous agent holds a high-impact tool with no human-approval gate.",
        tool_ev(offending) + [ev("autonomy", str(autonomy))],
        "Add a human-approval gate on high-impact tools, or reduce agent autonomy to human-in-the-loop.")

    # C-TOOL-02 (Moderate) over-broad tool scope (least privilege)
    broad = [t for t in tools if t.get("scope_broad")]
    add("C-TOOL-02", "Over-broad tool scope (least privilege)", "Moderate", bool(broad),
        "One or more tools are granted a scope broader than the declared purpose.",
        [ev(f"tools[{t.get('name','?')}]", f"scope={t.get('scope','?')}") for t in broad],
        "Narrow each tool grant to the minimum scope the declared purpose requires.")

    # C-GRD-01 (High) missing output guardrail/DLP for sensitive data
    grd01 = dclass in SENSITIVE_CLASS and not (grd.get("output_filter") or grd.get("dlp"))
    add("C-GRD-01", "No output guardrail/DLP for sensitive data class", "High", grd01,
        "The agent handles a sensitive data class with no output filter or DLP guardrail.",
        [ev("data_classification", str(dclass)), ev("guardrails", "output_filter/dlp absent/false")],
        "Enable an output filter / DLP guardrail appropriate to the data classification handled.")

    # C-GRD-02 (High) missing prohibited-behavior refusal for a declared prohibited surface
    grd02 = bool(prohibited) and not grd.get("prohibited_behavior_refusal")
    add("C-GRD-02", "No prohibited-behavior guardrail for a declared surface", "High", grd02,
        "A prohibited-behavior surface is reachable with no refusal guardrail configured.",
        [ev("prohibited_surface", ", ".join(prohibited)), ev("guardrails.prohibited_behavior_refusal", "absent/false")],
        "Configure a refusal/guardrail for each declared prohibited surface (e.g., financial/legal/tax advice, money movement).")

    # C-PROMPT-01 (Moderate) no instruction-source boundary while untrusted input is present
    prm01 = (not agent.get("instruction_source_boundary")) and has_untrusted
    add("C-PROMPT-01", "No instruction-source boundary", "Moderate", prm01,
        "The system prompt does not separate trusted instructions from untrusted retrieved/tool content.",
        [ev("instruction_source_boundary", "absent/false")]
        + ([ev("untrusted_input_surfaces", ", ".join(surfaces))] if surfaces else []),
        "State in the system prompt that tool/retrieved/user content is data, not instructions, and must not be executed.")

    # C-FAIL-01 (Moderate) no fail-closed / no human escalation on uncertainty
    fail01 = not (fail.get("fail_closed") and fail.get("human_escalation"))
    add("C-FAIL-01", "No fail-closed / escalation on uncertainty", "Moderate", fail01,
        "The failure mode does not fail closed and/or does not escalate to a human on uncertainty.",
        [ev("failure_mode", "fail_closed/human_escalation absent/false")],
        "Configure the agent to fail closed and escalate to a human when identity, source, or authorization is uncertain.")

    # C-EVAL-01 (Moderate) no evaluation coverage
    eval01 = not obs.get("eval_harness")
    add("C-EVAL-01", "No evaluation/benchmark coverage", "Moderate", eval01,
        "No evaluation harness is wired for this agent.",
        [ev("observability.eval_harness", "absent/false")],
        "Wire an evaluation/benchmark suite (route to ai-evaluation-benchmark-builder) before deployment.")

    # C-OBS-01 (Low) insufficient audit logging of tool calls
    obs01 = not obs.get("logs_tool_calls")
    add("C-OBS-01", "Insufficient tool-call audit logging", "Low", obs01,
        "Tool calls are not logged, limiting auditability and incident response.",
        [ev("observability.logs_tool_calls", "absent/false")],
        "Enable durable audit logging of every tool call with inputs, outputs, and identity.")

    fired = [f for f in findings if f["fired"]]
    fired_ids = [f["control_id"] for f in fired]

    # deterministic rating = highest fired severity (documented in references/domain-rules.md)
    max_rank = max([SEV_RANK[f["severity"]] for f in fired], default=1)
    rating = RANK_SEV[max_rank] if fired else "Low"

    if rating in ("Critical", "High"):
        disposition = "Remediate-before-deploy (recommended)"
    elif rating == "Moderate":
        disposition = "Conditional-remediation (recommended)"
    else:
        disposition = "Proceed-with-standard-controls (recommended)"

    severity_counts = {sev: sum(1 for f in fired if f["severity"] == sev)
                       for sev in ("Critical", "High", "Moderate", "Low")}

    data_gaps = [b for b in OPTIONAL_BLOCKS if b not in agent]
    if "untrusted_input_surfaces" not in agent:
        data_gaps.append("untrusted_input_surfaces")

    return {
        "review_id": doc.get("review_id"),
        "agent_id": agent_id,
        "as_of": as_of,
        "control_catalog_version": doc.get("control_catalog_version"),
        "findings": findings,
        "fired_findings": fired_ids,
        "severity_counts": severity_counts,
        "data_gaps": data_gaps,
        "recommended_rating": rating,
        "recommended_disposition": disposition,
        "adjudication_note": ADJUDICATION_NOTE,
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "agent_review_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
