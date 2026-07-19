---
name: ai-incident-investigator
description: >-
  Investigate AI, model, and agent incidents — harmful, incorrect, unauthorized, biased,
  privacy, security, or resilience events — by preserving evidence and building a durable
  case: an ordered chronology, the implicated model/agent and parties, an impact estimate,
  a documented severity, candidate root-cause HYPOTHESES, and routed remediation
  recommendations. Use when an AI incident responder, model-risk analyst, or compliance
  reviewer needs to reconstruct what an AI system did, assemble a cited evidence bundle,
  score severity, and route containment/remediation to the right owners. HARD BOUNDARY:
  this skill produces evidence and recommendations only — it NEVER closes an incident,
  determines a root cause, authorizes redeployment, files a regulatory/breach notification,
  exonerates a model, or writes a system of record; every disposition is a RECOMMENDATION
  pending human adjudication by the AI governance / model risk committee.
license: MIT
compatibility: Amazon Quick Desktop; requires model-registry, data-catalog/lineage, evaluation-harness, agent/tool-log, policy-library, and risk/issue-management MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Data, AI & Model Governance"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Investigate & casework"
  aws-fsi-agent-pattern: "Case agent + evidence bundle"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Confidential"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "AI / Model Risk Governance"
  aws-fsi-primary-user: "AI incident response / model risk / compliance"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# AI Incident Investigator

## Purpose and outcome
Take a reported AI/model/agent incident and make it adjudicable: reconstruct what the
system did, preserve the evidence, and assemble a durable case. For each incident the skill
emits a `case_id`, an ordered **chronology**, the implicated model/agent and **parties**,
an **impact estimate** (affected population, exposure, data classification), a documented
**severity**, **candidate root-cause hypotheses** (labeled as hypotheses, never findings),
and **routed remediation recommendations**. The outcome is an audit-ready evidence bundle
and a disposition **recommendation** — the substantive determination, closure, redeployment
decision, and any regulatory notification stay with human owners.

## Use when
- "Investigate this AI incident / what did the model or agent actually do?"
- "Preserve the evidence and build a chronology for this model incident."
- "Score the severity of this agent incident and tell me who should remediate it."
- "The chatbot exposed another customer's data — assemble the case for review."
- "An agent took an action outside its approved scope — reconstruct and route it."

## Do not use
- **First-line detection / alert enrichment** (queueing raw signals) → upstream monitoring
  or, for security-flavored signals, `security-alert-triage-assistant`.
- **Root-cause determination, incident closure, or redeployment sign-off** → the human AI
  governance / model risk committee; this skill only recommends.
- **Independent model revalidation** → `model-validation-assistant`.
- **Regulatory/breach notification drafting or filing** → legal/compliance and the Data
  Protection Officer; never produced or filed here.
- Personalized investment, legal, or tax advice → refuse.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Detection/triage and investigation are
**separate control activities**. This skill is the *investigation*: it consumes a reported
incident and emits a durable `case_id` + evidence bundle, then routes remediation to owners.
Common downstream routes (recommendations, not actions): `model-change-impact-analyzer`,
`model-validation-assistant`, `model-risk-documenter`, `ai-risk-assessment-builder`,
`prompt-and-agent-risk-reviewer`, `agent-permission-scope-reviewer`,
`data-quality-issue-investigator`, `data-lineage-documenter`,
`data-loss-prevention-incident-assistant`, `cyber-incident-response-coordinator`,
`operational-resilience-reporter`, `operational-risk-event-analyzer`, and
`agent-audit-trail-reviewer`. The investigation itself never performs the owner's work.

## Inputs and prerequisites
- The incident bundle: `incident_id`, `detected_at`, `incident_class`, the implicated
  `model_or_agent` (ref/name/version/owner), timeline `events[]` (each with `ts`,
  description, and a `source_ref`), an `affected` impact block, an optional
  `root_cause_hypothesis_category`, and related prior incidents. Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Read access to the model registry, data catalog/lineage, evaluation harness, agent/tool
  logs, policy library, and risk/issue systems.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The risk/issue system is the
system of record for incident state; the model registry identifies the implicated
model/agent and version; agent/tool logs and the evaluation harness supply the timeline and
behavioral evidence; the data catalog/lineage supplies affected-data context. **Cite every
evidence item.** Severity and routing config are **versioned contracts**.

## Workflow
1. **Validate & scope** — run `validate_input`; confirm the implicated model/agent, the
   incident class, and that timeline events and impact are present. Unresolvable gaps become
   `needs-evidence` (do not guess).
2. **Reconstruct the chronology (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): orders the
   `events[]` into a cited chronology, assembles parties and the impact estimate, and links
   related prior incidents.
3. **Score severity (deterministic)** — documented mapping over incident class, affected
   population, financial exposure, customer impact, regulated-decision impact, data
   classification, reversibility, and detection latency; `privacy`/`security`/`unauthorized`
   raise a severity floor. Explainable inputs, not a black box. See
   [references/domain-rules.md](references/domain-rules.md).
4. **Advance hypotheses, not findings** — emit candidate root-cause **hypotheses** tied to
   evidence; the determination is reserved for humans.
5. **Recommend disposition & route** — assign one recommendation
   (`recommend-escalate-for-adjudication` | `recommend-containment-referral` |
   `recommend-remediation-owner` | `needs-evidence`) and route remediation to the owners in
   `handoffs.md`. Attach the durable `case_id` and cited evidence bundle.
6. **Never close or determine** — no closure, determination, filing, exoneration, or
   redeployment authorization.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check enforces: a durable `case_id` on every record; every chronology
entry and the bundle are cited; only recommendation dispositions are used; severity_band
ties out to the deterministic score + escalation floor; and no closure / determination /
filing / redeployment-authorization language. **Fail closed** on any miss.

## Human approval
`required`. Every disposition is a **recommendation**. Human owners — the AI governance /
model risk committee, and legal/compliance/DPO for notification — make the binding call:
incident closure, root-cause determination, model exoneration or redeployment, and any
regulatory or breach notification. This skill proposes evidence and routing; humans decide.

## Failure handling
- **Missing timeline or impact** → `needs-evidence`, list exactly what is missing; do not
  infer a chronology or an impact figure.
- **Ambiguous model/agent identity** → resolve against the registry; if unresolved, flag and
  stop rather than attribute to the wrong system.
- **Conflicting logs/sources** → cite both, keep the discrepancy in the chronology, escalate.
- **Suspected active security/privacy exposure** → `recommend-containment-referral` and route
  to `cyber-incident-response-coordinator` / `data-loss-prevention-incident-assistant`; the
  skill does not perform containment.
- **Tool timeout** → return the partial bundle with an explicit incomplete flag; assume no
  retry and no step-up authorization.

## Output contract
1. **Case view** — per incident: `case_id`, `incident_class`, severity band, disposition
   (recommendation), one-line cited reason.
2. **Evidence bundle** (per non-`needs-evidence` case) — chronology (cited), model/agent,
   parties (aggregate counts only), impact estimate, candidate root-cause hypotheses,
   recommended routing, linked prior incidents, citations.
3. **Needs-evidence list** — the exact gaps blocking investigation.
4. **Machine-readable** — the investigation records + bundles keyed by `case_id`.
5. **Standing note** — "Investigation evidence and recommendations only; no incident has
   been closed, no root cause determined, no regulatory notification filed, and no
   redeployment authorized. Disposition is pending human adjudication."
See [references/controls.md](references/controls.md).

## Privacy and records
**Confidential.** Include only aggregate affected-population counts and the minimum evidence
needed; never embed individual customer identities or the raw sensitive content that caused
the incident. Preserve the evidence bundle, citations, and severity/routing config versions
per records policy (potential litigation/regulatory hold). Log every read and every case
artifact with the investigator identity; treat agent/tool logs as chain-of-custody evidence.

## Gotchas
- **Recommendation ≠ determination.** Severity and hypotheses inform a human; naming a
  hypothesis is not concluding the cause.
- **Containment is a referral, not an action.** The skill routes to IR/DLP; it never
  isolates, disables, or redeploys a model or agent.
- **Preserve before you analyze.** Capture the agent trail and evaluation runs as evidence
  first; logs may roll off.
- **Class floors severity.** `privacy`, `security`, and `unauthorized` incidents carry a
  severity floor so a low headline score cannot bury a serious event.
- **Config is versioned.** Record the severity/routing config version on every case so the
  scoring is reproducible and reviewable.
