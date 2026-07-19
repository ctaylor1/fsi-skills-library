---
name: operational-risk-event-analyzer
description: >-
  Analyze an operational-risk loss or near-miss event: classify it against the Basel Level-1
  event-type and business-line taxonomy, quantify impact (gross loss, recoveries, net loss,
  indirect costs), map contributing causes to control themes and a People/Process/Systems/
  External root cause, raise regulatory-reporting and board-notification escalation
  candidates, and recommend remediation to track — every finding cited to a source record.
  Use when an operational-risk or control analyst asks "classify this loss event", "what's
  the root cause and control theme", "how material is this", "does this need regulatory or
  board escalation", or needs a review-ready op-risk analysis pack. Produces findings, cited
  evidence, escalation candidates, and remediation recommendations ONLY with mandatory human
  adjudication; it NEVER makes a risk determination, accepts residual risk, closes the event,
  files a regulatory report, posts a journal, updates the risk register, or writes any system
  of record.
license: MIT
compatibility: Amazon Quick Desktop; requires operational-risk/loss-event (GRC), incident-management, change-management, finance/GL, third-party-inventory, and approved-calculation MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Risk Management"
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
  aws-fsi-owner: "Enterprise Risk Management"
  aws-fsi-primary-user: "Operational-risk / business control analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Operational Risk Event Analyzer

## Purpose and outcome
Given a single operational-risk **loss or near-miss event**, produce a deterministic,
source-cited **analysis pack**: a Basel event-type/business-line **classification**, a tied-out
**impact quantification**, **control-theme and root-cause findings**, **escalation candidates**
(regulatory-reporting, board-notifiable), a **severity band**, and **remediation
recommendations**. A successful output lets an operational-risk or control analyst adjudicate
the event — confirm the classification and materiality, decide on escalation and remediation,
and update the system of record. The analysis is evidence and recommendation; **every decision
and every write remains human.**

## Use when
- "Classify this operational loss event and quantify the impact."
- "What is the root cause and which control themes failed?"
- "How material is this event — does it need regulatory reporting or board notification?"
- "Analyze this near-miss and recommend remediation to track."
- An analyst needs a consistent, cited op-risk write-up to attach to a case for adjudication.

## Do not use
- The user wants a **risk decision or action**: confirm/accept residual risk, **close the
  event/case**, **file** an operational-risk regulatory report, **post** a loss journal, or
  **update the risk register** → out of scope. Produce the analysis and route the decision to
  the human adjudicator / authorized system.
- The event is a **live cyber intrusion** needing coordinated response → route to
  `cyber-incident-response-coordinator`; for an AI/model failure → `ai-incident-investigator`.
- **Third-party/vendor** control assessment (root cause is a vendor) → `third-party-risk-assessor`.
- A **suspected financial-crime** dimension needing a SAR narrative → route to
  `suspicious-activity-report-drafter` (draft-only, human-filed).
- Portfolio-level **key-risk-indicator** trending rather than a single event →
  `key-risk-indicator-monitor`; **control self-assessment** refresh → `risk-control-self-assessment-assistant`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits an analysis pack with a
durable `analysis_id`; downstream escalation, casework, remediation-tracking, and reporting are
performed by humans and other skills. It must not duplicate their decision, closure, filing, or
system-of-record steps.

## Inputs and prerequisites
- One **operational-risk event record** with: `event_id`, `as_of`, `config_version`,
  `currency`, `event_source_ref` (citation to the loss-event system), `is_near_miss`,
  `reported_event_type` (Basel L1) and `reported_business_line`, occurrence/discovery dates,
  and a `description`.
- **Financials**: `gross_loss`, `recoveries[]` (amount, type, `source_ref`), `indirect_costs`,
  and — for a near-miss — `potential_loss`.
- **Contributing causes**: `causes[]`, each with a `cause_code`, a `description`, and a
  `source_ref` (so each control finding is citable). Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Read access to the loss-event/GRC, incident, change, finance/GL, and third-party systems;
  the approved versioned thresholds/mappings (see [references/domain-rules.md](references/domain-rules.md)).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The loss-event/GRC record is the
position of record for the event and its financials; incident/change/HR/finance systems supply
causal and cost evidence; reference data normalizes the Basel taxonomy; the versioned config
supplies thresholds and mappings. Cite every finding to a source row.

## Workflow
1. **Scope & validate** — confirm the event and load its record; run `validate_input`. Fail
   closed on structural errors; note data-quality warnings that make parts not-evaluable.
2. **Classify (deterministic)** — normalize `reported_event_type`/`reported_business_line`
   against the Basel taxonomy; anything off-taxonomy is reported `not_evaluable`, not guessed.
3. **Quantify impact (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): total recoveries,
   `net_loss = max(gross_loss − recoveries, 0)`, `total_impact = net_loss + indirect_costs`,
   and the banding amount (potential loss for a near-miss).
4. **Map causes to control themes** — each `cause_code` maps to a control theme and a
   People/Process/Systems/External root cause, with the cause's `source_ref` attached.
5. **Escalation candidates & severity** — raise regulatory-reporting and board-notifiable
   **candidates** and assign the severity band per the documented deterministic mapping. These
   are flags for a human adjudicator, never actions.
6. **Recommend remediation** — derive remediation **recommendations** from the control themes.
7. **Write the pack** — classification + impact + findings (cited) + escalation candidates +
   severity + remediation recommendations + data gaps + the mandatory-adjudication disclaimer.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py) after.
The output screen confirms: impact arithmetic ties out; the severity band equals the
deterministic mapping; escalation flags do not under-flag versus thresholds; every finding has
a cited evidence row; `requires_human_adjudication` is true; **no decision/closure/filing/
posting language** is present; and the standing disclaimer is present. Fail closed on any miss.

## Human approval
`required` (R3). Human adjudication is mandatory before **any** regulated decision, escalation,
filing, risk-register update, journal posting, control attestation, case closure, or other
system-of-record change. The skill only reads and analyzes; it stages nothing for execution and
takes no case action.

## Failure handling
- **Off-taxonomy event type/business line** → report `not_evaluable`; do not force a Basel
  category.
- **Near-miss without `potential_loss`** → materiality is `not_evaluable`; severity rests on
  escalators only; never fabricate a loss amount.
- **Unknown `cause_code`** → report it `not_evaluable`; do not invent a control theme.
- **Missing cause `source_ref`** → the control finding is uncitable and will fail output
  validation; surface the gap rather than emitting an uncited finding.
- **Ambiguous event identity** → stop and confirm; never analyze the wrong event record.
- **Stale/conflicting sources** → cite both; do not resolve silently.
- **Tool timeout** → return the analysis computed so far with a clear "incomplete" flag; assume
  no automatic retry.

## Output contract
1. **Summary** — event id, classification, severity band, escalation candidates, impact totals.
2. **Classification** — Basel L1 event type + business line (or `not_evaluable`).
3. **Impact** — gross loss, recoveries, net loss, indirect costs, total impact, banding amount.
4. **Findings** — per finding: type (classification / materiality / control), statement, root
   cause, and cited evidence row(s).
5. **Escalation candidates** — regulatory-reporting and board-notifiable flags (for human
   adjudication, not actions) with the thresholds used.
6. **Remediation recommendations** — one per control theme, phrased as recommendations.
7. **Data gaps / not-evaluable items.**
8. **Machine-readable** — the analysis core + `analysis_id` for downstream handoffs.
9. **Standing disclaimer** — "Analysis and recommendations only; not a risk decision or
   regulatory filing. … No case action has been taken."
See [references/controls.md](references/controls.md).

## Privacy and records
`Confidential`. Include only the event data needed to evidence a finding; avoid unnecessary
personal data about staff or customers named in incident records (reference roles/records, not
identities, where possible). Retain the analysis + citations + config version per records
policy; log the read and any adjudication approval. Never exfiltrate event or customer data.

## Gotchas
- **An analysis is not a decision.** Severity, escalation candidates, and recommendations
  inform a human adjudicator; they never confirm a loss, accept residual risk, escalate, file,
  or close.
- **Escalation candidates are flags, not filings.** "Regulatory-reporting candidate" means a
  human must decide whether and how to report — the skill never reports.
- **Tie out the money.** Net loss and total impact are recomputed in `validate_output`; a
  narrative figure that disagrees with the arithmetic fails closed.
- **Thresholds are versioned config**, owned by ERM — not tuned per event. Record the
  `config_version` so an analysis is reproducible.
- **Root-cause language is factual.** Describe what control failed; do not assign individual
  blame or infer intent (conduct findings route to the accountable manager, not a conclusion).
- **Near-miss ≠ zero risk.** A near-miss with a large potential loss can still be High/Critical
  via the escalators; do not understate it because no money moved.
