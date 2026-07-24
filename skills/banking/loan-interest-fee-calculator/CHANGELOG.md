# Changelog — loan-interest-fee-calculator

## [0.1.0] — 2026-07-20
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** deterministic, source-linked loan-servicing recalculation — interest accruals
  (four day-count conventions), fees (flat / percent), level-payment and interest-only
  amortization, settlement/payoff, pro-rata participation allocations, a variance report vs.
  booked amounts, and a reconciliation to approved-engine totals — as a draft for review.
- **Controls:** R2; HARD BOUNDARY — never post, apply, waive, reverse, or approve an
  adjustment (`action_taken: "none"`); no personalized financial/legal/tax advice; every
  input carries provenance + citation; rates bound to an approved rate-table version; NPI/PII
  handling; `external-delivery` approval.
- **Scripts:** `validate_input`, `calculate_or_transform` (deterministic recalculation
  engine), `validate_output` (independent formula tie-outs, variance/reconciliation math,
  provenance, reproducibility, prohibited posting/approval + advice screen, disclaimer).
- **Evaluations:** trigger/routing, golden workbook, deterministic script checks, fail-closed
  safety on a non-compliant fixture, prompt-injection and external-delivery authorization.
- **Handoffs:** route incomplete closing conditions to `loan-package-completeness-checker`
  and substantive servicing exceptions to `loan-servicing-exception-resolver`; upstream
  `credit-application-packager`; parallel `covenant-compliance-monitor`.

### Pending before release
- Domain SME (loan servicing / operations) blind review; day-count and participation
  convention review against the firm's servicing standard.
- Wire read-only loan-servicing, document-intelligence, rate-table, and approved-engine MCP
  integrations at deployment.
