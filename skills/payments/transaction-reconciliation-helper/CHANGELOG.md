# Changelog — transaction-reconciliation-helper

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `existing-updated` relative to
the AWS baseline — stronger break taxonomy, deterministic tie-outs, settlement-break routing,
and a proposed-only / no-posting guardrail).

- **Scope:** transaction-level matching across gateway, processor/acquirer, bank, ledger, and
  merchant records; break classification with lineage; tie-out to the cash position of record;
  PROPOSED resolution entries. Draft-only; no posting, no break closure.
- **Break taxonomy (deterministic):** `missing_record`, `unmatched`, `amount_mismatch`,
  `duplicate`, `currency_mismatch`, `status_mismatch`, `timing_difference`, `fee_variance` —
  each evidenced (see `scripts/calculate_or_transform.py`).
- **Tie-out identity:** `residual_before = target_total − ledger_total`;
  `residual_after = residual_before − net_proposed`; `tied_out = |residual_after| ≤ tolerance`.
- **Controls:** R2; hard boundary against posting/booking/finalizing, break closure, and
  resolving settlement-file breaks (routed to `settlement-break-reconciler` with no proposed
  entry); versioned-config tolerances only; `external-delivery` approval.
- **Scripts:** `validate_input` (record schema, single-source/currency/ledger warnings),
  matching + tie-out engine, `validate_output` (taxonomy, lineage, deterministic tie-out
  recomputation, routing, proposed-only + posting-language screen, disclaimer).
- **Evaluations:** trigger/routing, golden tie-out-to-zero case, thin-source edge, deterministic
  script checks, no-posting safety + injection, external-delivery authorization.
- **Handoffs:** `settlement-break-reconciler`, `payment-exception-investigator`,
  `iso-20022-message-interpreter`, `chargeback-dispute-packager`, `settlement-report-summarizer`.

### Pending before release
- Domain SME (payments operations) + control-owner blind review; journal-entry policy sign-off
  on the proposed-entry format.
- Confirm the versioned tolerance/expected-source config source and its owner.
- Wire read-only MCP integrations (gateway, processor, bank, ledger, config) at deployment.
