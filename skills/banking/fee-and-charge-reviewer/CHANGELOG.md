# Changelog — fee-and-charge-reviewer

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `existing-updated` relative to
the AWS baseline — stronger evidence traceability, deterministic outcome mapping, and a hard
no-legal-conclusion / no-refund-decision / no-fee-action guardrail).

- **Scope:** categorize posted fees, compare each to the disclosed fee schedule / product
  terms, and produce cited findings + neutral questions + a remediation-request draft.
  Read-only; no violation determination, no refund/credit decision, no fee action.
- **Comparison (deterministic):** `matches_disclosed`, `exceeds_disclosed`,
  `frequency_cap_exceeded` (per-day / per-period caps), `waiver_condition_may_apply`,
  `not_in_schedule` — each explainable and evidenced (posted row + disclosed term), with a
  fixed status precedence (see `scripts/calculate_or_transform.py`).
- **Controls:** R2; hard boundary against asserting a legal/regulatory violation, deciding or
  promising a refund/credit/adjustment, or reversing/waiving/crediting a fee; disclosed
  amounts, caps, and waivers come from the versioned schedule only; `external-delivery`
  approval.
- **Scripts:** `validate_input` (schedule + posted-fee schema, evaluability warnings), the
  comparison engine, `validate_output` (evidence/citation completeness, deterministic
  outcome tie-out, prohibited-language screen, disclaimer, questions + remediation present).
- **Evaluations:** trigger/routing, golden discrepancies case, no-schedule edge, deterministic
  script checks, no-violation/refund safety + injection, external-delivery authorization.
- **Handoffs:** downstream to `complaint-resolution-assistant`,
  `loan-servicing-exception-resolver`, `dispute-operations-assistant`,
  `chargeback-dispute-packager`, `merchant-fee-optimizer`, `bank-statement-analyzer`,
  `account-anomaly-screener`.

### Pending before release
- Domain SME (deposit/loan product & servicing) + control-owner blind review; conduct review
  of question/remediation language.
- Confirm the versioned fee-schedule/config source, its effective-dating, and its owner.
- Wire read-only MCP integrations (core-banking fees, product terms, CRM, loan servicing,
  config) at deployment.
