# Controls — bank-statement-analyzer

- **Risk tier:** R2 — analytical. **Action mode:** Read-only analysis.
- **Human approval:** `external-delivery` — required before the analysis is sent to a
  customer or written to a case/loan file / system of record.

## Prohibited (fail closed)

- No **lending / credit decision** or communication of one: approve, decline, "you qualify",
  "you are approved / pre-approved", "eligible for the loan/credit", "denied", "creditworthy".
- No **affordability or eligibility determination** ("you can afford", "affordability
  approved", "income verified for underwriting"). This skill extracts and calculates; a human
  (or `loan-affordability-precheck` for an *indicative* estimate) decides.
- No **personalized financial / investment / tax advice** or recommendation to act ("you
  should refinance / invest / take out / consolidate"). Explain figures, do not advise.
- No **fraud / AML determination** — route anomaly screening with a priority band to
  `account-anomaly-screener`; describe patterns factually, never assert intent.
- No **threshold tuning to the individual**; use only the versioned config.

## Required output screens (`scripts/validate_output.py`)

- Every extracted **income source, recurring obligation, and fee** has ≥ 1 cited evidence row
  with a non-empty citation; every **fired anomaly** has ≥ 1 cited evidence row.
- **Tie-outs** hold: `net_cash_flow == total_credits − total_debits`; reported income total ==
  sum of its evidence amounts; reported fee total == sum of its evidence amounts (to the cent).
- No **decision / advice language** (regex screen: "you qualify", "approved for", "eligible
  for the loan", "you are (pre-)approved", "denied", "creditworthy", "you can afford", "you
  should (refinance|invest|consolidate|take out)", "guaranteed approval", etc.).
- Standing **disclaimer** present: "Analysis and extracted figures only; not a lending
  decision, eligibility determination, or financial advice."
- **Confidence flags** included when any anomaly fired or a data-quality gap exists.

## Confidence & conduct

- Every categorization is **heuristic unless sourced**; surface an uncategorized ratio and
  label low-confidence figures rather than overstating precision.
- Describe patterns factually; avoid stigmatizing language about the customer's spending.

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII).** Mask account/card numbers to last 4.
- Minimize customer data to what evidences an extracted figure.
- Retain the analysis + citations + config version per records policy; log read + approval.

## Reproducibility

`analysis_id` binds output to the exact inputs, statement period, and **config version**;
re-running with the same inputs and config reproduces every figure and anomaly.
