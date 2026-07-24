---
name: loan-interest-fee-calculator
description: >-
  Recalculate loan interest, fees, amortization schedules, settlement/payoff figures, and
  participation allocations from executed agreements, servicing transactions, and approved
  rate tables, producing a source-linked, reproducible workbook with formula tie-outs, an
  assumptions register, a variance report vs. booked amounts, and an approved-engine
  reconciliation. Use when a loan-servicing analyst asks to
  recompute a loan's interest and fees, check an amortization schedule, quote a
  payoff/settlement, allocate participation interest pro-rata, or reconcile to the servicing
  ledger and approved engine. HARD BOUNDARY: models and reports only — it NEVER posts,
  applies, waives, reverses, or approves an adjustment to any account or system of record,
  and gives no personalized financial, legal, or tax advice. Route incomplete closing
  conditions to loan-package-completeness-checker and substantive servicing exceptions to
  loan-servicing-exception-resolver; any account change is a separate, human-authorized step.
license: MIT
compatibility: Amazon Quick Desktop; requires loan-servicing/core-banking, document-intelligence (executed agreements), approved rate-table, and approved-calculation MCP integrations, plus versioned loan-calc config (all read-only).
metadata:
  aws-fsi-category: "Banking"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Model & calculate"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 5 - 2026 industry expansion"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Banking product & credit operations"
  aws-fsi-primary-user: "Loan-servicing analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Loan Interest & Fee Calculator

## Purpose and outcome
Given a loan's executed terms, servicing transactions, and the approved rate tables in
effect, rebuild a **deterministic, source-linked recalculation workbook**: accrue interest
per period on the stated day-count convention, recompute fees, amortize the balance, quote a
settlement/payoff, allocate participation interest pro-rata, and compare every recomputed
figure to the servicing-booked amount and to the approved calculation engine — every number
tied out and every input cited. A successful output lets a loan-servicing analyst defend each
figure to a reviewer, surface booked-amount variances for human follow-up, and hand a
reproducible workbook (`calc_id`) to the servicing-exception and completeness workflows. The
**decision to change an account stays with an authorized human.**

## Use when
- "Recompute the interest and fees on this loan from the note and the servicing ledger."
- "Check / rebuild the amortization schedule and tell me the split of principal and interest."
- "Quote the payoff / settlement figure as of this date."
- "Allocate the participation interest pro-rata across the lead and the participants."
- "Reconcile our recomputed totals to the booked amounts and to the approved engine."
- A servicing analyst needs a defensible, reproducible workbook and a variance report.

## Do not use
- The request is to **post, book, apply, waive, reverse, credit, refund, or approve** an
  adjustment ("go ahead and correct the fee", "post the payoff") → **HARD BOUNDARY**;
  recalculate and report only, and route the action to an authorized human / workflow.
- A **substantive servicing exception** needing root-cause investigation and a staged
  correction → [`loan-servicing-exception-resolver`](references/handoffs.md).
- **Closing conditions are incomplete** — collateral, legal, signature, or expiration items
  still open, so the terms are not reliable to recalculate from →
  [`loan-package-completeness-checker`](references/handoffs.md).
- **Personalized financial, legal, or tax advice** ("should I refinance?") → out of scope.
- A **consumer-facing fee explanation** against disclosed terms → `fee-and-charge-reviewer`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Upstream skills supply the executed,
complete terms; this skill emits a tied-out workbook with a durable `calc_id`, `inputs_hash`,
`config_version`, and `rate_table_version`; downstream skills, authorized workflows, and
humans consume it without recomputing. It must not investigate exceptions, stage or approve
corrections, deliver the workbook, or post anything.

## Inputs and prerequisites
- **Loan identifier**, a **calc date**, and a durable **case id** (anchors the accrual
  windows, payoff date, and applicable rate-table version).
- **Executed terms** — rate basis, day-count convention, fee definitions, participation
  shares, amortization terms — from the note / credit agreement / participation certificate.
- **Approved rate tables** (`rate_table_version`) for the rates in effect on the calc date.
- **Servicing transactions** — booked balances, posted interest and fees, unapplied funds,
  payoff quote — as the `book_amount` figures to compare against.
- Optional **approved-engine totals** to reconcile the recomputed grand totals to.
- Each cited amount is `{value, provenance, citation}`. Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Read access to loan-servicing, document intelligence, approved rate tables, the approved
  calculation engine, and the versioned loan-calc config (see
  [references/source-map.md](references/source-map.md)).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The **executed agreement is the
anchor**; approved rate tables supply in-effect rates; the servicing ledger supplies booked
amounts to compare against; the approved engine supplies totals to reconcile to; versioned
config supplies day-count defaults, tolerance, and the materiality threshold. A recomputed
figure is only as good as its source — **cite every input with a date**; where a booked
amount conflicts with the agreement, the agreement anchors the recomputation and the booked
amount becomes a variance for human review, never silently adopted.

## Workflow
1. **Scope** — confirm loan, calc date, currency, `config_version`, `rate_table_version`, and
   which sections are in scope (interest, fees, amortization, settlement, participations).
2. **Validate input** — run [scripts/validate_input.py](scripts/validate_input.py); resolve
   errors, note warnings (missing provenance, unrecognized day-count, shares not summing to 1,
   missing versions).
3. **Recalculate (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): accrue interest,
   recompute fees, amortize, quote the payoff, allocate participation, and build the variance
   report and the reconciliation, each with tie-outs.
4. **Read the checks** — confirm every tie-out passes, participation allocations sum exactly,
   the amortization ends at zero, and every input is in the register with provenance +
   citation; note material variances.
5. **Write the workbook** — a plain-language narrative of the recomputed interest, fees,
   schedule, payoff, and allocations, the variance report and reconciliation, explicit
   inputs and sources, and the standing disclaimer. Post nothing; approve nothing.
6. **Route** — send incomplete closing conditions to `loan-package-completeness-checker` and
   material/substantive variances to `loan-servicing-exception-resolver`.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check **independently re-derives** every tie-out (interest from
`principal * rate * year_fraction(day_count)`; fees from the basis; amortization
interest/principal/payment and a zero ending balance; settlement from its signed components;
participation allocations summing exactly), confirms the variance-report and reconciliation
math, requires provenance + citation on every input and `calc_id` + `inputs_hash` +
`config_version`, screens the narrative for posting/approval and personalized-advice
language, requires `action_taken == "none"`, and requires the disclaimer. **Fail closed on
any miss.**

## Human approval
`external-delivery`: human review and approval are required before the workbook or payoff
quote is delivered to a borrower, participant, counterparty, or another system, or written to
any system of record. **Posting or approving any adjustment is out of scope entirely** — the
skill takes **no action** and makes **no servicing decision**. No approval is needed for the
analyst's own read.

## Failure handling
- **Missing/non-numeric input** → `validate_input` errors; do not guess a principal or rate.
- **Unsourced input** → warned on input, **rejected** on output; every number needs a source.
- **Unrecognized day-count** → warned; engine defaults to 30/360 — confirm the note's basis.
- **Shares do not sum to 1** → `validate_input` errors; a participation cannot be allocated.
- **Booked amount conflicts with the agreement** → keep the agreement figure, record the
  booked amount as a variance, cite both; route material variances out.
- **Incomplete closing conditions** → stop and route to `loan-package-completeness-checker`
  rather than recalculating from unreliable terms.
- **Tool timeout** → return the sections computed so far with an explicit "incomplete" flag.

## Output contract
1. **Summary** — loan (de-identified), calc date, currency, `config_version`,
   `rate_table_version`, and the recomputed interest, fee, payoff, and participation totals.
2. **Workbook** — per section: interest accruals (principal, rate, day-count, year fraction,
   amount); fees (basis, base, rate, amount); the amortization schedule (per-period interest,
   principal, payment, balance); the settlement component walk; and the participation
   allocations.
3. **Variance report** — each recomputed figure vs. the servicing-booked amount, the
   variance, and `match` / `variance` and `material` flags.
4. **Reconciliation** — recomputed grand totals vs. any stated approved-engine totals, with
   `reconciled` / `out-of-balance` status.
5. **Assumptions register** — every input with `provenance` + `citation`.
6. **Machine-readable** — the full workbook JSON with `calc_id`, `inputs_hash`,
   `config_version`, and `action_taken: "none"` for downstream skills.
7. **Standing disclaimer** — "Illustrative loan-servicing recalculation for analytical review
   only; not a posting, adjustment, waiver, reversal, or approval, and not financial, legal,
   or tax advice. Every figure is conditional on the cited agreement terms, servicing data,
   and approved rate tables, and a qualified human must review and separately authorize any
   account change."
See [references/controls.md](references/controls.md) and
[references/domain-rules.md](references/domain-rules.md).

## Privacy and records
Highly Confidential (customer NPI/PII). Loan data embeds borrower identity, balances, and
account numbers — treat the workbook, its inputs, `case_id`, and `calc_id` as need-to-know;
de-identify borrower data in examples and fixtures. Retain the workbook, its assumptions
register, `config_version`, and `rate_table_version` per records policy; log the read and any
external-delivery approval.

## Gotchas
- **A recalculation is not a correction.** A recomputed figure is analytical evidence
  conditional on the cited inputs; it is never a posting, a waiver, or an approval.
- **Day-count convention dominates interest.** 30/360, 30E/360, actual/360, and actual/365
  give different interest for the same window — use the note's stated basis, never a default.
- **The last participant carries the residual.** Pro-rata allocations round to cents; the
  final share absorbs the rounding so the syndicate total is exact — never invent a cent.
- **The agreement outranks the ledger.** A booked amount that conflicts with the executed
  terms is a variance for human review, not a number to adopt.
- **Amortization must end at zero.** The final period repays the exact remaining balance;
  a non-zero ending balance means the schedule is wrong.
- **Do not tune to a number.** Formulas, tolerances, the materiality threshold, and day-count
  conventions come from versioned config; never bend them to match a booked figure.
