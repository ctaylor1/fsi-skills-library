# Changelog — settlement-report-summarizer

All notable changes to this skill package. Versions follow semver in `aws-fsi-version`.

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `existing-no-changes`
relative to the AWS baseline; authored fresh here).

- **Scope:** informational, read-only settlement/payout summary with a gross-to-net tie-out
  and source-linked figures.
- **Triggers:** positive (summarize settlement/payout, explain fees, why deposit < sales);
  negative (fee optimization, reconciliation/break, exception, message decode) with routing
  to adjacent skills.
- **Controls:** R1; no fee/financial/tax advice and no settlement-determination
  (deterministic language screen), no amount invention, no batch/date merging;
  external-delivery human approval.
- **Tools/data:** read-only processor/acquirer settlement, bank/ISO-20022 statement,
  card-network fee schedules, document-intelligence; durable `snapshot_id`.
- **Scripts:** `validate_input.py` (schema, single settlement/date, citations, category
  taxonomy, data-quality warnings) and `validate_output.py` (gross-to-net tie-out, funding
  match, fee totals, effective-rate and brand-split tie-outs, citation coverage,
  advice/determination screen, disclaimer presence).
- **Evaluations:** trigger/routing, golden normal + multi-settlement edge, deterministic
  script checks, no-advice/no-determination safety, prompt-injection, external-delivery
  authorization.
- **Handoffs:** downstream to `settlement-break-reconciler`, `transaction-reconciliation-helper`,
  `payment-exception-investigator`, `payment-failure-diagnoser`, `iso-20022-message-interpreter`,
  `merchant-fee-optimizer`, `chargeback-dispute-packager`.

### Pending before release
- Domain SME + control-owner blind review; accessibility review of the output format.
- Wire read-only MCP integrations (settlement, bank/ISO-20022, fee schedules) at deployment.
- With/without benchmark vs. no-skill baseline.
