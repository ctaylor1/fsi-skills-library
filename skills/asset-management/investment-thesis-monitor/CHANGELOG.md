# Changelog — investment-thesis-monitor

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). Scheduled, read-only,
alert-only thesis monitor for an asset-management research book.

- **Scope:** freshness-gated, explainable confirming/challenging signals + cited evidence +
  deterministic escalation band + deduplicated review queue. Read-only; no decision, trade,
  rebalance, thesis close/retire, system-of-record write, or investment advice.
- **Signals (deterministic):** `kpi_miss`/`kpi_beat`, `catalyst_missed`/`catalyst_met`,
  `estimate_revision_down`/`estimate_revision_up` (direction-aware), `stop_breach`/
  `price_target_breach`, `risk_news` — each explainable, evidenced, and gated on data
  freshness (see `scripts/calculate_or_transform.py`).
- **Controls:** R2; scheduled `read-only-monitoring`; `action_taken` always `none`; hard
  boundary against any position/thesis action or advice; versioned-config tolerances only;
  deduplication to protect escalation latency; `external-delivery` approval.
- **Scripts:** `validate_input` (snapshot schema, freshness/evaluability warnings), signal +
  escalation + dedup + queue engine, `validate_output` (freshness handling, dedup/queue
  packaging, deterministic escalation tie-out, no-autonomous-action + advice screen,
  disclaimer, durable `monitor_run_id`).
- **Evaluations:** trigger/routing (to `earnings-results-analyzer`,
  `investment-committee-memo-builder`, `fund-commentary-drafter`, `mandate-compliance-monitor`);
  golden Elevated + confirming + dedup + freshness-gap queue; deterministic script checks;
  no-autonomous-action safety + injection; external-delivery authorization.
- **Handoffs:** downstream to `earnings-results-analyzer`, `scenario-sensitivity-generator`,
  `dcf-modeler`, `coverage-initiation-researcher`, `performance-attribution-builder`,
  `investment-committee-memo-builder`, `fund-commentary-drafter`; sibling monitors
  `mandate-compliance-monitor`, `counterparty-exposure-monitor`; trade/close-thesis/advice to
  the human PM / trading desk / licensed professional.

### Pending before release
- Domain SME (research/investment) + control-owner blind review; precision/recall tuning of
  tolerances against a labeled backtest of real thesis breaks.
- Confirm the versioned tolerance/escalation config source and its owner.
- Wire read-only MCP integrations (thesis register, PMS/OMS, market data, research/estimates,
  config) and the scheduled runner cadence at deployment.
