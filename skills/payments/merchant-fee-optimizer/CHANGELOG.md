# Changelog — merchant-fee-optimizer

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `existing-updated` relative to
the AWS baseline — stronger evidence, transparent-assumption estimates, and no-guarantee /
no-binding-decision guardrails).

- **Scope:** decompose merchant card-processing fees (interchange, assessments, processor
  markup, fixed fees) and estimate transparent, evidenced savings opportunities. Read-only;
  no guarantee, no contract/processor action, no legal/tax/accounting advice.
- **Opportunities (deterministic):** `pricing_model_switch` (markup vs interchange-plus
  benchmark), `downgrade_recovery` (interchange downgrades vs qualified category),
  `level_2_3_enablement` (commercial cards at Level 1) — each explainable, evidenced, and
  expressed as a low-to-point range (see `scripts/calculate_or_transform.py`).
- **Controls:** R2; hard boundary against guaranteeing savings and against directing a
  binding decision to sign/terminate/switch a processor or contract; no legal/tax/accounting
  advice; versioned-config benchmarks only; MID/PAN masking; `external-delivery` approval.
- **Scripts:** `validate_input` (statement schema, evaluability warnings), fee-decomposition
  and opportunity engine, `validate_output` (evidence/citation + assumption completeness,
  range enforcement, savings tie-out, no-guarantee/no-advice language screen, disclaimer).
- **Evaluations:** trigger/routing, golden three-opportunity case, missing-qualified edge,
  deterministic script checks, no-guarantee/no-advice safety + injection, external-delivery
  authorization.
- **Handoffs:** downstream to `settlement-break-reconciler`, `transaction-reconciliation-helper`,
  `settlement-report-summarizer`, `chargeback-dispute-packager`, `network-rules-change-tracker`,
  `iso-20022-message-interpreter`.

### Pending before release
- Domain SME (payments operations / pricing) + control-owner blind review.
- Confirm the versioned benchmark config source (markup benchmark, Level 2/3 bps, recoverable
  share, savings bands) and its owner, and wire current card-network interchange schedules.
- Wire read-only MCP integrations (statement/settlement, gateway detail, network rules,
  contract, config) at deployment.
