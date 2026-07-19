# Controls — credit-risk-portfolio-analyzer

- **Risk tier:** R3 — regulated / control decision support. **Action mode:** Read-only analysis.
- **Human approval:** `required` — a human credit-risk officer / credit risk committee must
  adjudicate before any credit decision, allowance/reserve determination, limit action,
  filing, case closure, or system-of-record change. This skill produces evidence and
  recommendations only; it decides and writes nothing.

## Prohibited (fail closed)

- No **credit decision**: approval, adverse action, denial, or limit grant/increase/reduction.
- No **allowance / reserve / provision** determination, booking, or charge-off.
- No **limit-breach disposition or waiver**, no exception sign-off, no **case/finding closure**.
- No **filing** (regulatory report, call report, disclosure) — draft-only routing to a human.
- No **posting or write** to any general ledger or risk system of record.
- No **PD/LGD re-estimation**; consume governed model outputs and flag stale/missing ones.
- No **threshold tuning to a name** to erase a breach; use only the versioned limits config.
- No **forward default assertion** about a named obligor; report metrics factually.

## Required output screens (`scripts/validate_output.py`)

- Every fired exception has ≥ 1 cited evidence row tracing to an exposure `source_ref`.
- `suggested_disposition` equals the deterministic mapping from exception severities
  (any critical → Elevated; else any exception → Watch; else Stable).
- No prohibited decision/closure/filing/system-of-record language (regex screen over
  narrative, findings, recommended reviews, and routing).
- Standing disclaimer present; human-adjudication note present; routing path present when
  exceptions fired.

## Fairness / conduct

- Do not use protected-class attributes or their proxies as risk drivers or in findings.
- Concentration and delinquency are portfolio structure facts; describe them without
  stigmatizing language about individual borrowers.

## Data classification, privacy, records

- **Confidential.** Exposure and obligor data are business-confidential; minimize obligor
  identifiers in output to what evidences an exception (obligor code + exposure id, not
  free-text borrower PII).
- Retain the analysis + citations + `config_version` + scenario name per records policy; log
  the read and any adjudication handoff.

## Reproducibility

`analysis_id` binds the output to the exact inputs, `as_of` date, **limits config version**,
and scenario. Re-running with the same inputs and config reproduces the metrics, exceptions,
and disposition exactly.
