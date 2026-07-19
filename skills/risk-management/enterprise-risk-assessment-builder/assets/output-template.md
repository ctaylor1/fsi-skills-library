# Enterprise Risk Assessment (DRAFT) — {{scope.entity}}

<!--
Approved template for enterprise-risk-assessment-builder.
Template version: erm-tmpl-2026.1
This is a DRAFT deliverable for human review. The skill fills every section below from
approved, cited inputs; it NEVER accepts a residual rating, approves/finalizes the
assessment, closes a risk, signs an attestation, or writes the risk system of record.
All ten section headings are REQUIRED and are checked by scripts/validate_output.py
(`sections` must contain every heading). Do not rename or remove sections.
-->

**Assessment ID:** {{assessment_id}}  ·  **Template version:** {{template_version}}  ·  **Scoring config:** {{config_version}}
**Status:** draft-for-review  ·  **Prepared:** {{prepared_date}}

> **Standing note:** Draft enterprise risk assessment for human review only; no risk has
> been accepted, no residual rating approved, no assessment finalized, and nothing filed or
> written to the risk system of record.

## Scope & Basis
Entity / business unit, assessment period, methodology basis (e.g., semi-annual management
self-assessment), scoring model version, and any scope exclusions. Every figure must be
traceable to a cited source in the Evidence Register.

## Risk Inventory
The risks in scope, each with `risk_id`, title, category, and accountable owner. One row per
risk; link to scenarios, loss events, controls, indicators, and treatment actions by ID.

| Risk ID | Title | Category | Owner | Linked scenarios / loss events |
| ------- | ----- | -------- | ----- | ------------------------------ |

## Inherent Risk Assessment
Inherent likelihood (1–5) and impact (1–5), the resulting score (L×I) and band
(Low / Moderate / High / Critical). State the rationale and its citation; do not assert a
rating without a source.

| Risk ID | Likelihood | Impact | Score | Inherent band | Rationale (cited) |
| ------- | ---------- | ------ | ----- | ------------- | ----------------- |

## Control Environment
Controls linked to each risk with design and operating effectiveness, whether the control is
**tested (proven)**, and its evidence reference. Control credit toward residual risk is taken
**only** for controls that are tested AND evidenced (untested or unevidenced controls earn no
credit and are flagged).

| Risk ID | Control ID | Design | Operating | Proven | Credited | Evidence ref |
| ------- | ---------- | ------ | --------- | ------ | -------- | ------------ |

## Residual Risk & Appetite
Residual band = inherent band reduced by the recorded control credit (deterministic mapping).
Compare to the category risk appetite and flag every residual **above appetite**. Residual
ratings are recommendations for human adjudication, not decisions.

| Risk ID | Inherent | Control tier / reduction | Residual band | Appetite | Over appetite? |
| ------- | -------- | ------------------------ | ------------- | -------- | -------------- |

## Key Risk Indicators
KRIs linked to each risk, current status/threshold state, and whether a breach is present.
Note where an over-appetite risk lacks a linked KRI.

| Risk ID | Indicator ID | Title | Status | Threshold breached? |
| ------- | ------------ | ----- | ------ | ------------------- |

## Treatment Actions
For every residual **above appetite**, the recorded treatment action(s) with owner, due date,
and status. A residual above appetite with no treatment action is a completeness failure and
must be surfaced, not hidden.

| Risk ID | Action ID | Treatment | Owner | Due | Status |
| ------- | --------- | --------- | ----- | --- | ------ |

## Evidence Register
Every citation used in the assessment: risk-register references, control-test evidence, KRI
snapshots, loss-event and scenario references, with dates/versions. Each rating, effectiveness
claim, and indicator value must trace to an entry here.

| Ref | Source system | Item | Date / version |
| --- | ------------- | ---- | -------------- |

## Limitations & Assumptions
Data gaps, untested controls (no residual credit taken), needs-evidence items, scope
exclusions, model assumptions, and any residual that could not be assessed against appetite.
Uncertainty is disclosed here — never resolved by guessing.

## Approvals & Attestations
Records the human approvals **required before this draft becomes anything more than a draft**.
The skill leaves every approval `pending`; a human adjudicates. The draft never self-approves,
accepts a rating, or attests.

| Approval role | Approver | Status | Date |
| ------------- | -------- | ------ | ---- |
| Risk & Control Owner (1st line) | | pending | |
| Enterprise Risk Management (2nd line) | | pending | |
| Risk Committee / CRO | | pending | |
