---
name: actuarial-data-lineage-checker
description: >-
  Reconcile actuarial source data — exposure, premium, loss, claim, and policy records —
  across periods and systems, and detect duplicates, missing periods, definition/version
  shifts, and unexplained period-over-period movement, producing a source-linked lineage and
  break packet for actuarial review. Use when an actuarial analyst or data steward asks to
  "check the reserve data", "reconcile the loss triangle inputs", "find data breaks before
  the actuarial run", or "validate exposure/premium lineage". HARD BOUNDARY: R2 reconcile-only
  — it NEVER alters source data, selects actuarial assumptions or methods, certifies reserve
  data, or issues an actuarial opinion; it classifies breaks and preserves lineage for a human.
license: MIT
compatibility: Amazon Quick Desktop; requires policy-admin / claims / actuarial data stores, a versioned data-definition registry, and deterministic-computation MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Insurance"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Reconcile & validate"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 5 - 2026 industry expansion"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Insurance underwriting & claims"
  aws-fsi-primary-user: "Actuarial analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Actuarial Data Lineage Checker

## Purpose and outcome
Deterministically reconcile actuarial input data across periods/sources and classify breaks —
duplicates, missing periods, definition/version shifts, unexplained movement — each with cited
lineage. A successful output gives an actuary a defensible data-quality packet before a model
run; it never corrects data, chooses assumptions, or certifies reserves.

## Use when
- "Check/validate the reserve or triangle input data", "reconcile exposure/premium/loss lineage".
- "Find data breaks before the actuarial run", "did a data definition change between periods".

## Do not use
- The user wants to **correct/alter source data** → out of scope; the data owner acts.
- **Select assumptions/methods or run the model** → `actuarial-model-run-assistant`.
- **Reserving analysis / development** → `reserving-analysis-assistant`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Emits a break/lineage packet with a
durable `lineage_id`; it does not correct data or run models.

## Inputs and prerequisites
- Current and prior datasets keyed by (entity, metric, period), with value, `definition_version`,
  and source; expected periods; movement thresholds (versioned config). Schema:
  [scripts/validate_input.py](scripts/validate_input.py); rules:
  [references/domain-rules.md](references/domain-rules.md).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The system-of-record dataset is
authoritative; the data-definition registry supplies versions; config supplies thresholds. Cite
every break to its record(s) and definition version.

## Workflow
1. **Validate input** — run `validate_input`.
2. **Reconcile (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): detect duplicates,
   missing periods, definition shifts, and unexplained movement (> threshold without a
   documented reason). Preserve lineage per break.
3. **Assemble the packet** — breaks by type with evidence, plus a coverage summary.
4. **Validate output** — run [scripts/validate_output.py](scripts/validate_output.py) for break
   evidence/citation coverage, the no-alter/no-certify screen, and disclaimer.

## Validation loop
`validate_input` before, `validate_output` after. If a break lacks citation, or the text asserts
a correction/assumption/certification, **fix or fail closed**.

## Human approval
`external-delivery`: human review before delivery or a system-of-record write. No data is ever
altered and no reserve data is certified.

## Failure handling
- **Missing prior/expected periods** → report as missing-period breaks; do not infer values.
- **Definition version absent** → flag as not-evaluable for the definition-shift check.
- **Zero prior value** → guard division; classify as new/appearing rather than infinite movement.
- **Stale/conflicting source** → cite both; flag. **Tool timeout** → partial + incomplete flag.

## Output contract
1. **Summary** — as-of, config version, counts by break type, records checked.
2. **Breaks** — per break: type, key, metric, period, detail (expected vs actual), citation.
3. **Not-evaluable checks / data gaps.**
4. **Machine-readable** — breaks + `lineage_id`.
5. **Standing disclaimer** — "Data-lineage and break evidence only; no source data has been
   altered, no actuarial assumption selected, and no reserve data certified."
See [references/controls.md](references/controls.md).

## Privacy and records
Customer NPI/PII. Mask policy/claim identifiers. Retain the packet + citations + config version.
Log read + external-delivery approval. Never exfiltrate or alter source data.

## Gotchas
- **A break is not a correction.** Flag it with lineage; the data owner/actuary resolves it.
- **Definition shifts are silent killers.** A metric that changed definition between periods can
  look like real movement — always report the version change explicitly.
- **New vs moved.** A metric appearing this period with no prior is "new", not an infinite move;
  don't divide by a zero prior.
- **Unexplained ≠ wrong.** Report movement above threshold with missing documentation factually;
  the actuary judges.
