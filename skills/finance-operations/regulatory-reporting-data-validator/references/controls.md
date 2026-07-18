# Controls — regulatory-reporting-data-validator

- **Risk tier:** R2 — analytical. **Action mode:** Read-only analysis.
- **Human approval:** `external-delivery` — required before the findings pack goes outside
  the preparation team or is written to a case/system of record.

## Prohibited (fail closed)

- No **filing determination**: never state or imply that a report **is** accurate, correct,
  complete, compliant, "approved for filing", "cleared for filing", or "ready to file".
- No **certification or attestation** of accuracy/completeness on behalf of a person or the
  entity (the officer certification is a human control, not an agent output).
- No **sign-off** on the filing or **submission/transmission** of the report to a regulator.
- No **GL/journal posting** or correction — route reconciliation breaks to `gl-reconciler`;
  this skill only flags them.
- No **tolerance/threshold tuning** to make an exception disappear — use only the versioned
  config.
- No **opaque pass/fail** presented as decisive; findings are explainable and evidenced.

## Required output screens (`scripts/validate_output.py`)

- Every fired finding has ≥1 cited evidence row and a named basis.
- Readiness band equals the deterministic mapping from the fired-findings set
  (`Blocked` if any blocking finding, else `Review` if any advisory finding, else `Clear`).
- No certification/approval/filing/submission language (regex screen: "approved for filing",
  "cleared for filing", "ready to file", "we/i certify", "certified accurate", "we attest",
  "signed off on the report", "we filed/submitted", "submit the report to the regulator",
  "final and accurate", "the report is accurate/correct/compliant", etc.).
- Standing disclaimer present: "Validation findings and cited evidence only; not a filing
  determination, certification, or submission. No regulatory report has been certified,
  signed off, filed, or submitted."
- Remediation prompts included when any finding fired.

## Blocking vs. advisory (see domain-rules.md)

- **Blocking**: `completeness`, `lineage_completeness`, `edit_checks`,
  `reconciliation_tie_out`, `range_checks`, `sign_off_completeness`,
  `segregation_of_duties`, `timeliness` (overdue). Any of these ⇒ `Blocked`.
- **Advisory**: `variance_vs_prior`, `timeliness` (due-soon). Only these ⇒ `Review`.

## Segregation of duties & sign-off integrity

- Enforce that the required sign-off roles are present, dated on/after the data `as_of`, and
  that the preparer is not also the approver (configurable). SoD and timing exceptions are
  blocking evidence exceptions.

## Data classification, privacy, records

- **Confidential (financial records).** Mask entity identifiers (last segment of RSSD/LEI).
- Minimize data in the output to what evidences a fired finding.
- Retain findings + citations + `config_version` per records policy; log read + approval.

## Reproducibility

`validation_id` binds the output to the exact inputs, reporting instructions, and **config
version**; re-running with the same inputs and config reproduces the findings and readiness
band. No randomness, no model-scored severity — the band is a deterministic function of the
fired checks.
