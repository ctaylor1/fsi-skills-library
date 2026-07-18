---
name: model-inventory-maintainer
description: >-
  Create or update model and agent inventory records — ownership, purpose, lineage,
  materiality tier, dependencies, versions, approvals, and lifecycle status — by
  reconciling a proposed record against the model registry, data catalog, evaluation
  harness, and agent/tool logs, then surfacing gaps, discrepancies, and a deterministic
  materiality tie-out with cited evidence. Use when a
  model owner, validator, or AI-governance analyst asks to "onboard this model to the
  inventory", "update the inventory record", "check the model/agent inventory for gaps",
  "what materiality tier is this model", or needs a review-ready inventory change proposal
  for SR 11-7 model-risk or AI-governance oversight. This skill produces PROPOSED inventory
  entries, findings, and a materiality recommendation for human adjudication; it NEVER posts
  to the inventory system of record, approves/attests/certifies a model, clears a model for
  production, closes a finding, or files anything — those are Model Risk Governance decisions.
license: MIT
compatibility: Amazon Quick Desktop; requires model-registry, data-catalog, evaluation-harness, agent/tool-log, policy-retrieval, and risk/issue-tracker MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Data, AI & Model Governance"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 1 - platform controls"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Confidential"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "AI / Model Risk Governance"
  aws-fsi-primary-user: "Model-risk management / AI governance"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Model Inventory Maintainer

## Purpose and outcome
Given a proposed new or updated **model/agent inventory record** and the authoritative
sources it should reflect (model registry, data catalog, evaluation harness, agent/tool
logs, policy, risk/issue systems), assemble a **review-ready inventory change proposal**:
completeness against the required attribute set, a **deterministic materiality tie-out**,
lifecycle-transition validity, source reconciliation with a typed **break taxonomy**, and
findings — each with cited evidence. A successful output lets Model Risk Governance
adjudicate a single, well-evidenced change. The proposal is **PROPOSED only**: the skill
never posts to the inventory, approves a model, or closes a finding.

## Use when
- "Onboard this model/agent to the inventory" or "register it in the inventory."
- "Update the inventory record — owner, version, lineage, dependencies, lifecycle status."
- "Check the inventory record for gaps / does it reconcile with the registry and catalog?"
- "What materiality tier is this model/agent under our rubric?"
- A validator or governance analyst needs a cited, consistent change proposal to adjudicate.

## Do not use
- The user wants the inventory **posted/updated in the system of record**, a model
  **approved/attested/certified**, cleared for production, or a finding **closed** → out of
  scope; produce the proposal and route to Model Risk Governance for adjudication.
- **Model validation** (soundness, performance, conceptual review) → `model-validation-assistant`.
- **Model risk documentation** (model documentation, SR 11-7 write-ups) → `model-risk-documenter`.
- **Change-impact analysis** for a proposed model change → `model-change-impact-analyzer`.
- **AI risk assessment / use-case intake** for a new use case → `ai-risk-assessment-builder`
  or `ai-use-case-intake-classifier`.
- **Data lineage authoring** in depth → `data-lineage-documenter`; **agent permission scope**
  review → `agent-permission-scope-reviewer`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits an inventory change
proposal with a durable `proposal_id`; upstream intake/assessment skills supply the record
context and downstream validation/documentation skills consume the inventory identifier. It
must not duplicate their determinations or perform the adjudication/posting itself.

## Inputs and prerequisites
- A `record_id` (model/agent identifier), `change_type` (`create` | `update`), and
  `asset_kind` (`model` | `agent`).
- A `proposed_record` with the inventory attributes (name, owner, purpose, lifecycle status,
  materiality factors, versions, dependencies, lineage, approvals). For `update`, the
  `current_record` too. Schema: [scripts/validate_input.py](scripts/validate_input.py).
- **Evidence rows** mapping attributes to source citations, plus **authoritative source
  snapshots** (registry/catalog/eval/agent-log) for reconciliation.
- The versioned materiality/lifecycle **config** and its `config_version` (see
  [references/domain-rules.md](references/domain-rules.md)). Read-only access only.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The **model registry** is the
position of record for identity/version/owner; the **data catalog** is authoritative for
lineage/datasets; the **evaluation harness** for performance/eval evidence; **agent/tool
logs** for agent capability/tool scope. The inventory is a derived record — cite every
proposed attribute to a source; when the proposed record and a source conflict, record the
break and do not silently overwrite either.

## Workflow
1. **Scope & validate** — confirm `record_id`, `change_type`, `asset_kind`; load the
   proposed record, current record (for updates), evidence, and source snapshots; run
   [scripts/validate_input.py](scripts/validate_input.py).
2. **Compute (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to derive:
   completeness vs the required attributes; the **materiality tier** from documented factors
   per the versioned rubric; **lifecycle-transition validity**; and **source reconciliation**
   with typed breaks. Each output carries its evidence and citations.
3. **Assemble findings** — one finding per gap / discrepancy / invalid transition, with
   severity and cited evidence; record the materiality tie-out (computed vs proposed).
4. **Draft the proposal** — a PROPOSED record (status forced to `proposed`), the findings,
   the reconciliation table, and an explicit `requires_adjudication` flag naming the
   adjudication owner. No posting, no approval.
5. **Write the pack** — plain-language summary + findings + reconciliation + tie-out +
   standing disclaimer + explicit open questions for the adjudicator.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check confirms: `status` is `proposed` and `requires_adjudication` is
true; the computed materiality tier ties out to the rubric applied to the recorded factors;
every finding has ≥1 cited evidence row; every reconciliation break is typed from the
taxonomy; the standing disclaimer is present; and no autonomous-decision / posting /
approval / closure / filing language appears. Fail closed on any miss.

## Human approval
`required` (R3): Model Risk Governance must adjudicate before any inventory record is
posted, any model is approved/attested, any lifecycle state is committed, or any finding is
closed. The skill never performs the write and never assumes step-up authorization. No
approval is needed for the analyst's own read of the proposal.

## Failure handling
- **Missing required attributes** → record a completeness finding; do not fabricate values.
- **No source snapshot for an attribute** → mark it `unverifiable`; do not assert a match.
- **Ambiguous / duplicate `record_id`** → stop and confirm; never merge the wrong record.
- **Stale source snapshot** (older than the configured window) → flag `stale`; cite both
  dates; do not silently trust it.
- **Invalid lifecycle transition** → flag it; never normalize it to a "valid" one.
- **Conflicting sources** → record the break; do not resolve silently.
- **Tool timeout** → return the partial proposal computed so far with an `incomplete` flag.

## Output contract
1. **Summary** — record (masked as needed), change type, computed materiality tier, count of
   findings, `requires_adjudication: true`, named adjudication owner.
2. **Materiality tie-out** — factors, score, computed tier vs proposed tier (per rubric).
3. **Completeness** — required attributes present / missing.
4. **Lifecycle** — from → to and whether the transition is valid.
5. **Reconciliation** — per attribute: inventory value, source value, system, result, and
   typed break.
6. **Findings** — per finding: attribute, severity, description, cited evidence.
7. **Machine-readable** — the proposal core + `proposal_id` for downstream skills.
8. **Standing disclaimer** — "Proposed inventory changes and findings only; not an approval,
   attestation, or system-of-record update. Model Risk Governance adjudication is required
   before any change is posted."
See [references/controls.md](references/controls.md).

## Privacy and records
**Confidential.** Inventory records may reference proprietary model logic, third-party
terms, and owner identities — minimize to what the change requires. Mask personal
identifiers where an owner is an individual (retain role/contact per policy). Retain the
proposal + citations + `config_version` for reproducibility; log the read and the
adjudication decision (made by the human, not the skill). Never exfiltrate registry, catalog,
or eval contents.

## Gotchas
- **A proposal is not a posting.** High completeness or a clean tie-out never means the record
  is approved or in the inventory — adjudication and the write are human.
- **Materiality is a rubric, not a vibe.** The tier comes from the documented factors and the
  versioned config; do not talk an owner up or down a tier. A single high factor
  (regulatory use, full autonomy) escalates to Tier 1 by rule.
- **Agents are inventory too.** Autonomous/tool-using agents get a record: capabilities, tool
  scope, and permissions are attributes; do not treat "it's just an agent" as out of scope.
- **Reconciliation direction matters.** "Missing in inventory" and "missing in source" are
  different breaks with different owners — type them, don't collapse them.
- **Lifecycle is a state machine.** Not every status can follow every other; `retired` is
  terminal. Flag invalid jumps rather than normalizing them.
- **Config is a versioned contract.** Record the `config_version`; a proposal must be
  reproducible from the same inputs and rubric version.
