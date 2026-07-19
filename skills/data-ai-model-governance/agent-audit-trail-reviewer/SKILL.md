---
name: agent-audit-trail-reviewer
description: >-
  Review an AI agent's run audit trail — prompts and instructions, retrieved sources, tool
  calls, human approvals, outputs, overrides, and records retention — for reproducibility
  and control effectiveness, and produce a findings pack with cited evidence and a triage
  disposition. Use when an internal auditor, compliance-monitoring analyst, or AI-governance
  reviewer asks "review this agent run's audit trail", "did the required controls operate",
  "is this run reproducible", "were the tool calls in scope", "was there an unapproved
  action or override", or needs review-ready, evidenced findings for an agent or model run.
  HARD BOUNDARY: this skill produces evidence and recommendations for a human adjudicator
  only; it NEVER attests control effectiveness, makes a compliance determination, closes or
  files a finding, or writes to the audit/risk/issue system of record — those are
  human/authorized-system actions.
license: MIT
compatibility: Amazon Quick Desktop; requires model-registry, data-catalog, evaluation-harness, agent/tool-log, policy-retrieval, and risk/issue-register MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Data, AI & Model Governance"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Confidential"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "AI / Model Risk Governance"
  aws-fsi-primary-user: "Internal audit / compliance monitoring / AI governance"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Agent Audit Trail Reviewer

## Purpose and outcome
Given an AI agent's **run audit trail**, evaluate a fixed set of **reproducibility** and
**control-effectiveness** checks, attach cited evidence to every finding, and produce a
review-ready findings pack with a **triage disposition band**. A successful output lets an
internal auditor, compliance monitor, or AI-governance reviewer see exactly which controls
operated, where the trail is incomplete or a control did not fire, and what to adjudicate —
the **determination, the issue filing, and any control attestation remain human**.

## Use when
- "Review this agent run's audit trail for control effectiveness."
- "Is run R-771 reproducible from what we logged?"
- "Were the agent's tool calls within its approved scope?"
- "Did every gated action have a human approval before it executed?"
- "Was any guardrail or approval overridden, and by whom?"
- An auditor or model-risk reviewer needs consistent, cited findings to attach to a review.

## Do not use
- The user wants a **control attestation, a compliance determination, or a pass/fail
  verdict** ("attest the control is effective", "sign off this run") → out of scope; produce
  evidenced findings and route to the human adjudicator.
- The user wants a finding **closed, filed, or logged** in the risk/issue system → out of
  scope; that is a human/authorized-system action.
- The task is a full **incident investigation** (harm/unauthorized/biased/privacy/security
  event, evidence preservation, remediation coordination) → `ai-incident-investigator`.
- The task is a deep **prompt/guardrail/injection design review** of the agent itself →
  `prompt-and-agent-risk-reviewer`.
- The task is a **tool-by-tool least-privilege entitlement map** → `agent-permission-scope-reviewer`.
- The trail implicates an **undocumented model/agent change** → `model-change-impact-analyzer`.
- The agent/model is missing or wrong in the **inventory** → `model-inventory-maintainer`.
- A **data defect** (not an agent-control gap) drives the concern → `data-quality-issue-investigator`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a cited findings pack
with a durable `review_id` and stops. Downstream investigation, permission-scope,
incident, and change-impact skills consume the `review_id` rather than re-deriving findings.
It never duplicates their disposition, closure, or filing steps.

## Inputs and prerequisites
- The **run audit trail** for one agent run: run header (model/prompt/config identifiers,
  seed/temperature, timestamps) plus an ordered `events[]` list of prompt, retrieval,
  tool_call, approval, override, output, and retention events. Schema and field detail:
  [scripts/validate_input.py](scripts/validate_input.py) and
  [references/source-map.md](references/source-map.md).
- The applicable **agent-audit policy version** and the run's **control config**
  (allowed tools, required reproducibility fields, action classes that require approval,
  objects that must be retained). Thresholds are versioned config, not per-run judgment —
  see [references/domain-rules.md](references/domain-rules.md).
- Read access to model registry, data catalog, evaluation harness, agent/tool logs,
  policies, and the risk/issue register (read-only).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The **agent/tool log** is the
event record of what happened; the **model registry and policy** define what *should* have
happened (required controls, allowed tools, retention). Where the log and the registry/policy
conflict, cite both and flag for the reviewer — never resolve silently. Every finding cites
the specific event(s) behind it.

## Workflow
1. **Scope & validate** — confirm the run and load its trail; run
   [scripts/validate_input.py](scripts/validate_input.py). Fail closed on structural
   problems; note data-quality warnings that make some checks not evaluable.
2. **Evaluate controls (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to compute the
   reproducibility and control-effectiveness checks (see domain-rules). Each finding returns
   a fixed severity and the evidence events behind it. Checks are **explainable rules**, not
   an opaque score.
3. **Assemble evidence** — for each finding, attach the specific events and the policy/config
   expectation it deviates from, with citations.
4. **Suggest disposition** — map the finding-severity profile to a disposition band
   (No exceptions noted / Review / Escalate) per the documented mapping. This is a triage
   suggestion for a human adjudicator, explicitly **not** an attestation or determination.
5. **Write the pack** — plain-language finding descriptions + cited evidence + advisory
   recommendations + the standing disclaimer + explicit benign explanations to check
   (e.g., an approval logged out-of-band, retention captured in a separate system).

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output screen confirms: every finding has cited evidence; each severity equals
the deterministic mapping for its type; the disposition maps deterministically from the
severity counts; the reproducibility block is coherent; `human_adjudication_required` is
true; the standing disclaimer is present; and **no autonomous decision, closure, filing, or
attestation language** is present. Fail closed on any miss.

## Human approval
`required`: this is R3 decision-support. Every finding requires **human adjudication** before
any regulated decision, control attestation, issue filing, closure, or system-of-record
write. The skill never attests, decides, closes, files, or writes — it produces evidence and
recommendations only. No approval is needed for the reviewer's own read of the pack.

## Failure handling
- **Missing/incomplete trail** (no prompt, no retention, missing reproducibility fields) →
  report the affected checks as **not evaluable** or as reproducibility findings; do not
  infer a control operated when the trail does not evidence it.
- **Ambiguous run/agent identity** → stop and confirm; never review the wrong run.
- **Log vs. registry/policy conflict** → cite both; do not resolve silently.
- **Structural malformation** (missing required event fields, dangling approval reference) →
  `validate_input` fails closed; the run is not reviewed until corrected.
- **Tool timeout / partial trail** → return the findings computed so far with a clear
  "incomplete — not all events evaluated" flag; never present a partial review as complete.

## Output contract
1. **Summary** — run/agent (identifiers), policy version, finding counts by severity,
   suggested disposition band, reproducibility complete/incomplete.
2. **Findings** — per finding: id, type, control domain, severity, factual description,
   cited evidence event(s), and an advisory recommendation (route/escalate to a human).
3. **Reproducibility** — present vs. missing required fields.
4. **Consider (benign explanations)** — alternatives a reviewer should check before
   adjudicating (out-of-band approval, cross-system retention, expected scope).
5. **Machine-readable** — findings + evidence + `review_id` for downstream skills.
6. **Standing disclaimer** — "Control-review evidence only; not a control attestation or
   adjudication. No finding has been closed, filed, or written to a system of record; human
   adjudication is required."
See [references/controls.md](references/controls.md).

## Privacy and records
Confidential. The trail may embed prompts, retrieved content, and outputs containing
customer or model IP. Minimize reproduced content to what evidences a finding; cite event
IDs and refs rather than pasting payloads. Mask any identifiers the trail exposes. Retain the
review + citations + policy version per records policy; log the read and any adjudication
hand-off. Never exfiltrate trail content to a non-approved destination.

## Gotchas
- **A finding is not a determination.** Findings and a disposition band justify *review and
  escalation*, never a control attestation, a compliance verdict, or a closure.
- **Absence of evidence is a reproducibility/retention finding, not a clean pass.** If the
  trail does not record an approval, treat it as *missing approval to adjudicate*, and prompt
  the reviewer to check for an out-of-band approval — do not assume it happened.
- **Severity and disposition come from the versioned config, not from the run.** Do not tune
  thresholds to make a run look better or worse.
- **Describe control gaps factually.** Say "no recorded human approval event", not "the agent
  broke the rules" or "the control failed" — attribution of a control failure is the
  adjudicator's call.
- **Out-of-band controls exist.** An approval or retention record may live in another system;
  the pack flags the gap in *this* trail and invites the reviewer to reconcile.
