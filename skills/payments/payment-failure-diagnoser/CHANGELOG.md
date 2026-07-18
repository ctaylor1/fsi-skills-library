# Changelog — payment-failure-diagnoser

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `existing-updated` relative to
the AWS baseline — stronger trace completeness, deterministic routing, and a hard
no-action / no-fraud-or-sanctions-determination guardrail).

- **Scope:** end-to-end trace of a failed/rejected/returned/stuck payment, rail-specific
  reason-code interpretation, root-cause determination, and a single deterministic
  suggested route. Read-only; no repair, resubmission, reversal, release, refund, or filing.
- **Reason-code interpretation (deterministic):** bundled representative code sets for
  ISO 8583 (card), NACHA (ACH), and ISO 20022 pacs.002 status reasons, each mapped to a
  root-cause category (see `scripts/calculate_or_transform.py` and
  `references/domain-rules.md`).
- **Routing (deterministic):** root-cause category → exactly one downstream route
  (payment-exception-investigator, payment-repair-assistant, iso-20022-message-interpreter,
  payment-fraud-case-investigator, dispute-operations-assistant, or customer-remediation),
  plus a `retry_eligible` read from the same versioned config.
- **Controls:** R2; hard boundary against payment actions (modify/repair/resubmit/reverse/
  release/cancel/return/refund) and fraud/sanctions determinations; versioned code-set and
  route config only; cautions required for duplicate/re-presentment and screening-hold risk;
  `external-delivery` approval.
- **Scripts:** `validate_input` (trace schema, evaluability warnings), interpretation +
  routing engine, `validate_output` (root-cause evidence, per-leg interpretation, route and
  retry tie-outs, action/determination-language screen, disclaimer, required cautions).
- **Evaluations:** trigger/routing, golden format-reject (RC01 → repair route), stuck-in-flight
  and unknown-code edges, deterministic script checks, no-action/no-determination safety +
  injection, external-delivery authorization.
- **Handoffs:** triage → investigation → repair chain; downstream to
  `payment-exception-investigator`, `payment-repair-assistant`, `iso-20022-message-interpreter`,
  `payment-fraud-case-investigator`, `dispute-operations-assistant` /
  `chargeback-dispute-packager`.

### Pending before release
- Domain SME (payments operations & network rules) + control-owner blind review.
- Confirm the versioned code-set and root-cause→route config sources and their owners.
- Wire read-only MCP integrations (processor/scheme trace, settlement/ledger, code-set
  reference, ISO 20022 parser, config) at deployment.
