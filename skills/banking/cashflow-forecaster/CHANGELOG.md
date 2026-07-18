# Changelog — cashflow-forecaster

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `existing-updated` relative to
the AWS baseline — stronger tie-outs, assumption provenance, and no-advice / no-guarantee
guardrails).

- **Scope:** transparent base/upside/downside cash-flow forecast from transaction history +
  user assumptions, with drivers, an uncertainty band, and per-scenario tie-outs. Draft-only;
  no advice, no credit decision, no system-of-record write.
- **Model (deterministic):** period spread of history, recurring inflow/outflow averages,
  net-flow volatility, ranked drivers, versioned scenario factors, one-off assumptions applied
  at a period offset, running-balance projection (see `scripts/calculate_or_transform.py`).
- **Controls:** R2; hard boundary against financial/investment/tax/credit advice, credit or
  eligibility decisions, and guarantees of future balances; versioned-config scenario factors
  only; assumption provenance required; `external-delivery` approval.
- **Scripts:** `validate_input` (schema, thin-history/assumption warnings), forecast engine,
  `validate_output` (scenario completeness, tie-outs, monotonicity, provenance, no-advice
  screen, disclaimer, drivers).
- **Evaluations:** trigger/routing, golden three-scenario case with fixed expected balances,
  thin-history edge, deterministic script checks, no-advice safety + injection,
  external-delivery authorization.
- **Handoffs:** downstream to `financial-spreading-assistant`,
  `retirement-income-scenario-modeler`, `financial-goal-progress-analyzer`, and licensed
  advisory / lending workflows; upstream from `bank-statement-analyzer` and RM copilots.

### Pending before release
- Domain SME (banking analytics) + control-owner blind review; conduct/fairness review of
  drivers and scenario presentation.
- Confirm the versioned scenario-factor/tolerance config source and its owner.
- Wire read-only MCP integrations (transactions/balances, product terms, CRM, document
  intelligence, config) at deployment.
