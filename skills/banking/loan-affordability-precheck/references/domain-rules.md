# Domain Rules — loan-affordability-precheck

Explainable affordability **metrics** and how they map to an **indicative affordability band**.
Thresholds are configuration (versioned, owned by credit policy / product terms), not hard-coded
judgments, and are **never tuned to an individual applicant**. The band is a triage signal for a
human underwriter — it is **not** a credit approval, denial, eligibility/qualification finding, or
adverse-action decision.

## Inputs (see `scripts/validate_input.py`)

- **loan**: `type` (`mortgage` | `auto` | `personal`), `principal`, `annual_rate_pct`,
  `term_months`, and for a mortgage the monthly escrow parts `monthly_tax`, `monthly_insurance`,
  `monthly_hoa`.
- **income**: `gross_monthly`, optional `other_monthly`, optional `net_monthly`.
- **obligations**: `existing_monthly_debt` (non-housing recurring debt), `existing_housing_expense`
  (current rent/mortgage), `monthly_living_expenses`.

## Deterministic computation (see `scripts/calculate_or_transform.py`)

| Quantity | Formula |
| -------- | ------- |
| Monthly rate `r` | `annual_rate_pct / 100 / 12` |
| Principal & interest | `P·r / (1 − (1+r)^−n)`, `n = term_months`; if `r = 0`, `P / n` |
| Proposed payment | P&I `+` escrow (escrow = tax + insurance + HOA; mortgage only) |
| Housing payment | mortgage: the proposed payment; else: `existing_housing_expense` |
| Total obligations | mortgage: `housing + existing_monthly_debt`; else: `existing_housing + existing_monthly_debt + proposed_payment` |
| Front-end DTI | `housing_payment / total_gross_monthly` |
| Back-end DTI | `total_obligations / total_gross_monthly` |
| Residual income | `(net_monthly or gross) − total_obligations − monthly_living_expenses` |

`total_gross_monthly = gross_monthly + other_monthly`. When `net_monthly` is absent, residual uses
gross income and is labelled **indicative only** (residual is conventionally an after-tax measure).

## Indicative band mapping (deterministic, documented)

| Band | Rule (all thresholds from versioned config) |
| ---- | ------------------------------------------- |
| **Within typical guidelines** | `front_end_dti ≤ frontend_dti_max` (default 0.28) AND `back_end_dti ≤ backend_dti_max` (default 0.36) AND `residual_income ≥ residual_income_min` (default 800) |
| **Approaching typical limits** | Not "Within", AND `back_end_dti ≤ backend_dti_stretch` (default 0.43) AND `residual_income ≥ 0` |
| **Outside typical guidelines** | Otherwise (`back_end_dti > backend_dti_stretch` OR `residual_income < 0`) |

The band names deliberately describe *distance from typical policy thresholds*, not an outcome.
"Within typical guidelines" does **not** mean approved; "Outside typical guidelines" does **not**
mean denied. Only a human underwriter, applying the full policy and verified data, decides.

## Stress cases (always produced)

- **Rate up**: recompute the payment at `annual_rate_pct + bump` for each `stress_rate_bumps_pct`
  (default +2%, +3%); re-derive DTIs, residual, and band.
- **Income down**: reduce gross (and the net basis) by each `stress_income_haircuts_pct`
  (default −10%, −20%) with the payment held; re-derive DTIs, residual, and band.

Each scenario reports its own metrics and band so the reviewer sees sensitivity, not a single point
estimate.

## Hard boundaries (fail closed)

- Never state or imply **approval, denial, pre-approval, qualification, eligibility, or
  adverse-action** — those are binding credit decisions reserved for a human underwriter and the
  loan-origination system.
- Never present the band or a stress result as a **decision or commitment to lend**.
- Never **tune thresholds to the applicant** or infer "what should qualify"; use only the versioned
  config and record its `config_version`.
- Never give **personalized borrowing/investment advice** ("you should take this loan / borrow
  against X").
- Do not use protected-class attributes or proxies (ECOA/Reg B fair-lending): the inputs are income,
  expenses, debt, and product terms only.

## Reproducibility

The pack carries the `loan` inputs, resolved `thresholds`, and `config_version`. Re-running the same
inputs and config reproduces the payment, DTIs, residual, band, and every stress scenario;
`validate_output.py` re-derives the payment and each band as an independent tie-out.
