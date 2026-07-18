# Changelog — credit-memo-drafter

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). Drafts a commercial
credit memorandum from an approved credit package as decision-support for a human underwriter.

- **Scope:** compute DSCR, leverage, LTV, and collateral coverage from cited inputs; tie the
  recomputed ratios back to the approved spread; check policy coverage and covenant headroom;
  document exceptions with mitigants; assemble a template-conformant, fully cited draft memo.
  Draft-only; the finished memo is *proposed* to the underwriter via the approval broker.
- **Controls:** R3; no credit decision, pricing, booking, funding, filing, or system-of-record
  write; no granting/waiving of exceptions or covenants; approvals recorded as `pending` only
  (no self-grant); `unsupported_assertions` must be empty; spread tie-out must reconcile;
  decision/closure/filing/booking/waiver language screen; versioned policy/template config.
- **Scripts:** `validate_input` (request-bundle schema, needs-data warnings), drafting engine
  (metrics + tie-out + policy coverage + covenant headroom + section assembly + pending
  approvals), `validate_output` (draft disposition, required-section coverage, citation/
  traceability, empty unsupported-assertions, tie-out, pending-approvals, decision-language
  screen, standing note).
- **Evaluations:** trigger/routing, golden memo exercising every section and control,
  deterministic script checks, a non-compliant memo that fails closed, prompt-injection and
  decision refusals, and an approval-authorization refusal.
- **Handoffs:** upstream `financial-spreading-assistant`, `bank-statement-analyzer`,
  `cashflow-forecaster`, `credit-application-packager`; downstream
  `loan-package-completeness-checker`, `covenant-compliance-monitor`,
  `credit-risk-portfolio-analyzer`; the credit decision is a human underwriting action.

### Pending before release
- Credit-policy owner + underwriting/credit-risk blind review; segregation-of-duty review.
- Confirm the credit-memo template, policy thresholds, and approval-authority matrix source,
  owner, and versioning.
- Wire read-only MCP integrations (loan origination, approved spread, document intelligence,
  credit policy, covenant/collateral, risk rating, CRM) at deployment.
