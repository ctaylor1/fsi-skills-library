---
name: bank-statement-analyzer
description: >-
  Extract income, recurring obligations, cash-flow trends, fees, and factual anomalies from
  one or more bank statements, with every figure source-linked to the statement line it
  derives from and flagged for confidence. Use when a consumer, relationship manager, or
  credit analyst asks to "analyze this bank statement", "summarize my income and recurring
  bills", "extract cash-flow trends", "total the account fees", or needs a source-linked
  statement spread for onboarding, servicing, or a credit review. This skill extracts and
  calculates only; it NEVER makes a lending, credit, affordability, or eligibility decision,
  NEVER gives personalized financial/investment/tax advice, and NEVER makes a fraud
  determination — those are human or adjacent-skill actions.
license: MIT
compatibility: Amazon Quick Desktop; requires core-banking (statements/transactions), document-intelligence, CRM, product-terms/reference, and approved-calculation MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Banking"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 1 - stabilize existing"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "existing-updated"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Banking product & credit operations"
  aws-fsi-primary-user: "Consumer / relationship manager / credit analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Bank Statement Analyzer

## Purpose and outcome
Given one or more bank statements (as ledger rows or a parsed document), extract a
**source-linked statement spread**: income, recurring obligations, cash-flow trends, and
fees, plus **factual anomaly flags** — each figure cited to the statement line it derives
from and labeled with a confidence flag. A successful output lets a consumer understand
their cash flow, or gives a relationship manager / credit analyst a consistent, reproducible
spread to attach to an onboarding, servicing, or credit file. The extraction is the product;
every **decision** (lending, affordability, dispute, fraud) remains human or an adjacent skill.

## Use when
- "Analyze this bank statement / these last three statements."
- "Summarize my income and recurring bills; total the fees."
- "Extract cash-flow trends and flag anything unusual, with the evidence."
- A reviewer needs a cited, reproducible statement spread for a case or credit package.

## Do not use
- The user wants a **lending / credit decision**, an **affordability or eligibility
  determination**, or "do I qualify" → out of scope. Extract the figures and route the
  decision to a human underwriter; for an *indicative* (non-binding) estimate route to
  `loan-affordability-precheck`.
- **Fraud / unusual-activity screening** with a review-priority band → `account-anomaly-screener`.
- **Deep fee categorization, disclosure comparison, or a fee dispute** → `fee-and-charge-reviewer`.
- **Forward-looking projection** (base/upside/downside) → `cashflow-forecaster`.
- **Spreading into a credit-analysis template or tax-return spread** → `financial-spreading-assistant`;
  assembling a lending package/memo → `credit-application-packager` / `credit-memo-drafter`.
- **Personalized financial, investment, or tax advice** → not provided by any skill; refer to
  a licensed professional.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a statement-analysis
pack with a durable `analysis_id`; downstream affordability, spreading, forecasting, fee, and
anomaly skills consume it. It must not duplicate their decision, forecast, or dispute steps.

## Inputs and prerequisites
- Account identifier and the **statement period** (start/end) to analyze; one or more
  statements covering it.
- **Transaction rows** — each with `txn_id`, date, amount (non-negative), direction
  (debit/credit), and `source_ref`; optionally category, counterparty, and running balance.
  Opening/closing balances enable the cash-flow tie-out. Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Read access to core-banking statements/transactions (position of record); document
  intelligence when only a parsed document is supplied; CRM and reference/product terms for
  context; the versioned analysis config (see [references/domain-rules.md](references/domain-rules.md)).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The core-banking ledger is the
position of record; a parsed document supplies provenance only. CRM adds disclosed income and
known payees; reference data resolves categories and fee codes. Cite every figure to a
statement line; where ledger and document disagree, cite both and flag the discrepancy.

## Workflow
1. **Scope & validate** — confirm the account and statement period; load the rows; run
   `validate_input`. Resolve blocking errors; record data-quality warnings.
2. **Extract & calculate (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to compute income,
   recurring obligations, cash-flow trends (incl. the balance tie-out), fees, and factual
   anomaly flags. Each figure and flag returns its evidence rows and citations.
3. **Attach evidence** — for each income source, obligation, fee, and fired anomaly, attach
   the specific statement lines and the period/basis behind it.
4. **Flag confidence** — surface the uncategorized ratio, missing balances, thin baseline,
   partial coverage, and any ledger/document discrepancy; label low-confidence figures.
5. **Write the pack** — plain-language spread + the evidence + the confidence flags +
   explicit "not a decision / not advice" framing and the standing disclaimer.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check confirms: every income source / obligation / fee and every fired
anomaly has cited evidence; the tie-outs hold (`net_cash_flow == credits − debits`, income
and fee totals equal their evidence sums); no lending/affordability decision or advice
language is present; the standing disclaimer is present; confidence flags are included when
any anomaly fired. Fail closed on any miss.

## Human approval
`external-delivery`: human review required before the analysis is sent to a customer or
written to a case / loan file / system of record. No approval is needed for the reviewer's
own read. The skill never takes an account or lending action.

## Failure handling
- **Missing running balances / opening-closing** → report balance-based anomalies and the
  tie-out as not evaluable; do not fabricate balances.
- **Thin baseline** (few non-recurring debits) → `large_one_off_debit` is low-confidence;
  say so; do not overstate anomalies.
- **Uncategorized transactions** → classification is heuristic; surface the ratio and label
  affected figures low-confidence.
- **Ledger vs document conflict** → cite both; do not resolve silently.
- **Transactions outside the period** → flag rather than silently include.
- **Ambiguous account/identity** → stop and confirm; never analyze the wrong account.
- **Tool timeout** → return the figures computed so far with a clear "incomplete" flag.

## Output contract
1. **Summary** — account (masked), period, currency, net cash flow, count of fired anomalies.
2. **Income** — total, count, monthly average, per-source evidence rows (cited).
3. **Recurring obligations** — per counterparty: occurrences, mean, total, evidence (cited).
4. **Cash-flow trends** — total credits/debits, net, monthly rollup, and the balance tie-out.
5. **Fees** — total, count, evidence (cited).
6. **Anomalies** — per fired flag: name, factual reason, evidence (cited), confidence.
7. **Confidence flags** — data-quality limits on the figures above.
8. **Machine-readable** — the full core + `analysis_id` for downstream skills.
9. **Standing disclaimer** — "Analysis and extracted figures only; not a lending decision,
   eligibility determination, or financial advice."
See [references/controls.md](references/controls.md).

## Privacy and records
Customer NPI/PII. Mask account/card numbers (last 4). Minimize customer data in output to
what evidences an extracted figure. Retain the analysis + citations + config version per
records policy; log the read and any external-delivery approval. Never exfiltrate customer
data.

## Gotchas
- **Extraction is not a decision.** Cash-flow strength justifies *analysis*, never a lending,
  affordability, or eligibility conclusion — those route to a human or `loan-affordability-precheck`.
- **Categorization is heuristic.** A raw description isn't a category; keyword matching uses
  word boundaries (so "coffee" is not a fee) but can still miss — surface the uncategorized ratio.
- **Recurring ≠ variable.** A fixed obligation (rent, loan, subscription) recurs with a stable
  amount; variable spend at the same merchant is not an obligation. Config sets the tolerance.
- **Anomalies are factual, not fraud.** A negative-balance day, an NSF item, or a large debit
  is an observation; for a fraud/priority screen route to `account-anomaly-screener`, and
  never assert intent.
- **Tie-outs matter.** If `opening + net ≠ closing`, the extraction is wrong or the statement
  is incomplete — flag it rather than presenting figures that don't reconcile.
- **Do not tune to the person.** Categorization keywords and thresholds come from the approved
  versioned config, not from guessing what's "normal" for this customer.
