# Controls — cashflow-forecaster

- **Risk tier:** R2 — analytical / model. **Action mode:** Draft-only; no system-of-record change.
- **Human approval:** `external-delivery` — required before the forecast is sent to a
  customer or written to a case/plan/system of record. Internal analytical use may be
  reviewer-sampled.

## Prohibited (fail closed)

- No **financial, investment, tax, or credit advice** and no personalized recommendation to
  act ("you should invest / refinance / borrow / pay off / move your money").
- No **credit or eligibility decision** — never state or imply the customer is approved,
  pre-approved, qualifies, or is denied for a loan, line, mortgage, or overdraft.
- No **guarantee or promise of a future balance or outcome** ("guaranteed", "risk-free",
  "you will have at least $X", "this account will not overdraft"). A forecast is a range of
  estimates, not a certainty.
- No **hidden or per-user tuning** of scenario factors — factors come from the versioned
  config, not from guessing what a given customer's future "should" look like.
- No **system-of-record write** — the skill produces a draft artifact only.

## Required output screens (`scripts/validate_output.py`)

- All three scenarios (`base`, `upside`, `downside`) are present.
- Each scenario ties out: `opening_balance + sum(period net) == ending_balance`, and the
  ending equals the last period's running balance (tolerance 0.01).
- Scenario endings are monotonic: `downside <= base <= upside`.
- Every `assumptions_register` entry carries a non-empty `provenance`.
- No advice / guarantee / credit-decision language (regex screen over narrative + notes).
- Standing disclaimer present: "Forecast for planning purposes only; not financial,
  investment, tax, or credit advice, and not a guarantee of future account balances.
  Assumptions are estimates and actual results will vary."
- Drivers are reported whenever history exists.

## Reproducibility & tie-outs

- `history_tieout` reconstructs total historical net flow from the per-period spread and
  reconciles it to the raw sum of transactions (tolerance 0.01) — a formula-correctness gate.
- `forecast_id` + `config_version` make every scenario reproducible from inputs.

## Fairness / conduct

- Do not use protected-class attributes or proxies as drivers or assumptions.
- Present the downside scenario and the lowest-balance period plainly; do not bury shortfall
  risk, and do not overstate certainty in the base case.

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII).** Mask account numbers to last 4.
- Minimize customer data in the output to what the forecast needs (amounts, dates, drivers).
- Retain the forecast + assumptions + config version per records policy; log the read and
  any external-delivery approval. Never exfiltrate customer data.
