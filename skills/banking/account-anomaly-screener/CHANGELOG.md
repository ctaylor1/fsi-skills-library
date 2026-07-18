# Changelog — account-anomaly-screener

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `existing-updated` relative
to the AWS baseline — stronger evidence, escalation, and no-autonomous-fraud-decision
guardrails).

- **Scope:** explainable anomaly signals + cited evidence + suggested review priority.
  Read-only; no determination, no account action.
- **Signals (deterministic):** amount-vs-history, velocity, new high-value counterparty,
  geo/channel novelty, dormancy-reactivation, round-amount clustering, rapid in/out — each
  explainable and evidenced (see `scripts/calculate_or_transform.py`).
- **Controls:** R2; hard boundary against fraud/AML determination and account actions
  (block/freeze/close/reverse/file); versioned-config thresholds only; benign-explanation
  prompts required; `external-delivery` approval.
- **Scripts:** `validate_input` (activity schema, evaluability warnings), signal engine,
  `validate_output` (evidence/citation completeness, deterministic priority tie-out,
  determination-language screen, disclaimer, benign prompts).
- **Evaluations:** trigger/routing, golden Elevated case, thin-baseline edge, deterministic
  script checks, no-determination safety + injection, external-delivery authorization.
- **Handoffs:** downstream to `payment-fraud-case-investigator`,
  `suspicious-activity-report-drafter`, `chargeback-dispute-packager`,
  `dispute-operations-assistant`, `bank-statement-analyzer`.

### Pending before release
- Domain SME (fraud strategy) + control-owner blind review; fairness review of signals.
- Confirm the versioned threshold/priority config source and its owner.
- Wire read-only MCP integrations (transactions, CRM, reference data, config) at deployment.
