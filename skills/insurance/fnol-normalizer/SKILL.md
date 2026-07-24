---
name: fnol-normalizer
description: >-
  Normalize raw first-notice-of-loss (FNOL) intake into the standard claim schema —
  deterministically map free-text loss-type and cause values to the controlled vocabulary,
  validate required fields, check date sanity, and flag missing or unmappable values — producing
  a normalized record plus a cited exception list for a FNOL specialist to review. Use when an
  intake specialist asks to "normalize this FNOL", "standardize the loss codes", "clean up the
  intake record", or "check the FNOL for missing fields". HARD BOUNDARY: R3 decision-support
  only — it NEVER determines coverage, assigns liability or fault, sets a reserve, or opens/
  routes a claim as an action; it only standardizes and flags for a human. Routes damage-document
  review to claim-damage-evaluation-comparator.
license: MIT
compatibility: Amazon Quick Desktop; requires claims-intake records, controlled-vocabulary config, and reference-data MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Insurance"
  aws-fsi-skill-type: "Utility skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Domain workflow"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 5 - 2026 industry expansion"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Insurance underwriting & claims"
  aws-fsi-primary-user: "First-notice-of-loss specialist"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# FNOL Normalizer

## Purpose and outcome
Given a raw FNOL intake record, deterministically map free-text loss-type and cause values to the
controlled vocabulary, validate required fields, check date sanity, and surface every missing or
unmappable value with cited evidence. A successful output is a normalized record plus an
exception list a FNOL specialist reviews — coverage, liability, and reserve remain the human's.

## Use when
- "Normalize/standardize this FNOL", "clean up the intake record".
- "Standardize the loss/cause codes", "check the FNOL for missing required fields".
- Downstream claims steps need a schema-conformant, code-standardized intake record.

## Do not use
- The user wants a **coverage, liability, or reserve** determination → out of scope; the human
  decides.
- Damage-document comparison → route to `claim-damage-evaluation-comparator`.
- Fault/liability evidence mapping → `liability-evidence-matrix-builder`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Emits a normalized record with a durable
`normalization_id`; it does not open, route, or adjudicate a claim.

## Inputs and prerequisites
- The **raw_fnol** record and a **config** with controlled vocabularies (loss_type_map,
  cause_map) and required_fields. Schema: [scripts/validate_input.py](scripts/validate_input.py).
- Controlled-vocabulary config — a versioned contract. See
  [references/domain-rules.md](references/domain-rules.md).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The intake record is the system of
record; vocabularies from versioned config. Cite every mapping and exception to the raw field.

## Workflow
1. **Validate input** — run `validate_input`; confirm the raw record and config are present.
2. **Normalize (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): map loss_type/cause
   via the vocabularies, carry through plain fields, check required-field presence and
   loss/report date order.
3. **Assemble exceptions** — per exception: field, raw value, reason, citation.
4. **Suggest disposition** — `normalized` or `exceptions-for-review` (a triage suggestion, not a
   claims decision).
5. **Validate output** — run [scripts/validate_output.py](scripts/validate_output.py) for
   exception citation coverage, the no-adjudication screen, and disclaimer.

## Validation loop
`validate_input` before, `validate_output` after. If an exception lacks a citation, or the text
contains coverage/liability/reserve language, **fix or fail closed**.

## Human approval
`required`: no coverage, liability, or reserve determination, and no claim open/route action,
without a human. The skill only standardizes and flags.

## Failure handling
- **Unmappable code** → set canonical to null and flag `unmapped_code`; never guess a mapping.
- **Missing required field** → flag `missing_required`; do not fabricate a value.
- **Loss date after report date** → flag `date_order`; do not reorder silently.
- **Ambiguous free text** → flag; do not choose among candidate codes.

## Output contract
1. **Summary** — intake id (masked), disposition, exception count.
2. **Normalized record** — canonical fields with a per-field mapping log.
3. **Exceptions** — per exception: field, raw value, reason, citation.
4. **Machine-readable** — normalized + normalization_log + exceptions + `normalization_id`.
5. **Standing disclaimer** — "Intake normalization only; not a coverage, liability, or reserve
   determination and not a claim-handling decision. No claim has been opened, routed, or
   adjudicated."
See [references/controls.md](references/controls.md).

## Privacy and records
Customer NPI/PII. Mask claimant identifiers. Retain normalized record + mapping log + config
version. Log read + external-delivery approval. Never exfiltrate intake data.

## Gotchas
- **Normalization is not adjudication.** A clean normalized record says nothing about coverage.
- **Unmapped ≠ invalid**: an unmappable cause is flagged for a human to code, not dropped.
- **Never infer loss_type from the narrative** — map only the provided coded field; ambiguity is
  an exception.
- **Dates**: a loss-after-report ordering is a data-quality flag, not a fraud finding.
