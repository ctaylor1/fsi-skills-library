---
name: insurance-data-reconciler
description: "Reconcile supplied insurance premium, loss, exposure, policy and claim datasets; detect duplicate observations, missing periods/series, definition changes and unexplained movements on matching financial bases. Use for source lineage and data-quality evidence before insurance analysis or actuarial work; do not use to correct records, select actuarial assumptions or certify reserves."
license: MIT
compatibility: Python 3.10+; offline structured inputs and supplied source evidence. Expected source systems are not bundled production connectors.
metadata:
  aws-fsi-category: "Insurance"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Reconcile & validate"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Insurance Phase 1"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "existing-updated"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "Reviewed target-specific jurisdiction/product profiles required; fixture coverage is not global applicability"
  aws-fsi-owner: "Insurance data governance and actuarial data"
  aws-fsi-primary-user: "Actuarial analyst"
  aws-fsi-version: "0.2.0"
  aws-fsi-recertification-date: "2027-09-18"
---

# Insurance Data Reconciliation

## Purpose and outcome
Reconcile supplied insurance premium, loss, exposure, policy and claim data with explicit financial and definition bases. Produce a source-linked break packet and per-check evaluability. This is evidence preparation, not source correction, assumption selection or certification.

## Use when
Check insurance dataset lineage, missing observations, duplicates, definition changes and unexplained movement before analytics or actuarial work. Reuse across lines only when metric and accounting/date bases are explicit.

## Do not use
For source correction, ask the data owner. For reserving methods and model execution, route to `pc-reserving-analysis-assistant` or `pc-reserving-analysis-assistant`; reconciliation does not approve their inputs or methods.

## Adjacent-skill handoffs
Read [references/handoffs.md](references/handoffs.md). Carry the artifact and unresolved issues; the receiver validates its native schema and decides whether its particular analysis is evaluable.

## Inputs and prerequisites
Read [references/domain-rules.md](references/domain-rules.md) for row grain and schema. Supply current/prior observations, expected periods/series, definition and financial bases, configuration version, context and sources. Missing prior/expected coverage stays not evaluable.

## Source hierarchy
Read [references/source-map.md](references/source-map.md). External integrations are not bundled. Content hashes bind the supplied data but do not authenticate it.

## Workflow
1. Run `scripts/validate_input.py` on the supplied JSON; stop on structural or nonfinite-value errors.
2. Run `scripts/calculate_or_transform.py`. Duplicate current/prior records are not arbitrarily selected; non-comparable bases are withheld; absence never becomes zero.
3. Review break counts, comparisons, per-check states and unresolved issues. Duplicate findings retain every conflicting observation; basis conflicts are reported alongside duplicate ambiguity without selecting a row or calculating movement.
4. Run `scripts/validate_output.py`. Its callable `validate(output, input_doc)` additionally recomputes the expected result when original input is supplied.

## Validation loop
The executable regressions in `scripts/test_regressions.py` test missingness, duplicate ambiguity, zero baselines, removed observations and financial incompatibility. Schema passing and clean data do not certify downstream model quality.

## Human approval
Human review applies to externally delivered work within the user's authorization. This helper performs no external delivery or source mutation and produces no approval evidence.

## Failure handling
Report missing prior/expected coverage as non-evaluable checks, not fabricated missing-period rows. Report changed zero baselines as absolute movement with undefined percentage. Withhold mismatched currency/unit/date/definition/valuation bases. Preserve upstream issues.

## Output contract
A content-bound lineage ID, source-linked breaks, comparisons and check coverage accompany `clean`, `breaks-for-review` or `partial-not-evaluable`. `clean` requires complete context/provenance and all declared checks evaluated with no breaks. Read [references/insurance-contract.md](references/insurance-contract.md) for completeness/evaluability versus approval/execution.

## Privacy and records
Carry only authorized record identifiers and evidence needed for reconciliation. Retain supplied source/config versions under the deployment's records policy. No record is modified.

## Gotchas
A missing series is discoverable only if present in a prior snapshot or declared expected universe. A high movement can be valid; a documented explanation does not change the recorded value. Different valuation dates require a separately specified development/revision method, not this like-for-like comparison.
