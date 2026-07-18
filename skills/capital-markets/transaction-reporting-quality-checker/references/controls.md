# Controls — transaction-reporting-quality-checker

- **Risk tier:** R2 — analytical. **Action mode:** Read-only analysis.
- **Human approval:** `external-delivery` — required before the exception pack is delivered
  to compliance or written to the reporting case / system of record.

## Prohibited (fail closed)

- No **compliance/breach determination** or statement/implication that the firm **is** in
  breach, is non-compliant, or has committed a reporting violation.
- No **report action or recommendation to act**: submit, amend, cancel, resubmit, correct,
  or suppress a regulatory report; no self-report to a regulator.
- No **reportability decision** — never decide that a transaction "is not reportable"; that
  is a source/compliance attribute, not an inference this skill makes.
- No **attestation / sign-off / certification** that remediation is complete or the batch is
  clean.
- No **priority override** — the suggested remediation band comes only from the deterministic
  mapping of exception codes, not from judgement about the desk or the day.

## Required output screens (`scripts/validate_output.py`)

- Every exception has ≥1 cited evidence row and a recognized exception `code`.
- `suggested_priority` equals the deterministic mapping from the exception codes
  (blocking → **Blocking**; else high → **High**; else any → **Review**; else **Clean**).
- No determination/report-action language (regex screen: "in breach", "is non-compliant",
  "regulatory violation", "cancel/amend/resubmit the report", "submit the correction to the
  regulator", "certify remediation", "attest that", "no report required", "suppress the
  exception", "self-report to …").
- Standing disclaimer present: "Quality-control findings only; not a compliance
  determination. No regulatory report has been submitted, amended, cancelled, or suppressed."
- `false_positive_checks` included whenever any exception fired.

## Segregation of duties

- QC (this skill) is separate from **repair** (`trade-break-resolver`, R4), from **input
  validation** (`regulatory-reporting-data-validator`), and from **filing/exam packaging**
  (`regulatory-exam-response-packager`). This skill evidences; others repair, validate, or file.

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII).** Counterparty LEIs and possible national/client
  identifiers. Minimize client identifiers to what evidences an exception; mask or reference
  full national IDs rather than reproduce them.
- Retain the QC pack + citations + `config_version` per records policy; log read + approval.

## Reproducibility

`qc_id` binds the output to the exact batch, source, config version, and reference-data
snapshot; re-running with the same inputs reproduces the exceptions and the priority.
