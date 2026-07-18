# Controls — loan-affordability-precheck

- **Risk tier:** R3 — regulated / control decision support. **Action mode:** Read-only analysis.
- **Human approval:** `required` — a human underwriter must adjudicate before any credit decision,
  adverse-action notice, customer commitment, filing, or write to the loan-origination system of
  record. This skill **recommends and evidences; it never decides, closes, or files**.

## Prohibited (fail closed)

- **Credit decision** of any kind: approval, denial, pre-approval, conditional approval, or a
  statement/implication that the applicant **qualifies** or is **eligible/ineligible**.
- **Adverse-action** determination, notice, or reason codes (ECOA/Reg B, FCRA) — a declined
  applicant's notice is a human/authorized-system action, not an output of this skill.
- **Commitment to lend**, rate lock, or offer; the precheck is not an application decision.
- **Threshold tuning to the individual**; use only the versioned config.
- **Personalized borrowing/investment advice** ("you should take this loan / borrow against X").
- **Protected-class attributes or proxies** as inputs (fair-lending: ECOA/Reg B).

## Required output screens (`scripts/validate_output.py`)

- **Payment tie-out:** `baseline.proposed_payment` equals the amortized recomputation (+ escrow).
- **Band tie-out:** `baseline.affordability_band` — and every stress-scenario band — equals the
  deterministic mapping from its DTIs + residual against the carried, versioned `thresholds`.
- **Stress coverage:** at least one rate-stress and one income-stress scenario are present.
- **No credit-decision / adverse-action / qualification / directive-advice language** (regex screen;
  the standing disclaimer field is excluded from the scan).
- **Standing disclaimer present:** "Indicative affordability estimate only; not a credit decision,
  approval, denial, or adverse-action determination. Any lending decision requires human
  underwriting."
- **Assumptions block present and non-empty** (loan terms, escrow, residual basis, config version).

## Fair lending / conduct

- Inputs are income, expenses, debt, and product terms only — no protected-class attributes or
  proxies. Describe results factually; do not add discouraging or steering language.
- Present affordability neutrally; the band describes distance from policy thresholds, not a verdict.

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII).** Mask applicant/account identifiers to last 4.
- Minimize applicant data in output to what supports the estimate.
- Retain the precheck + inputs summary + `config_version` per records policy; log the read and any
  request for external delivery or system write (which requires human approval).

## Reproducibility

`precheck_id` binds the output to the exact inputs and **config version**; re-running with the same
inputs and config reproduces the payment, DTIs, residual, band, and stress scenarios.
