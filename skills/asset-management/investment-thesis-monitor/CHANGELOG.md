# Changelog

## 0.2.0 — 2026-09-20

- Adopt Phase 1 ownership and canonical naming; preserve alias metadata.
- Require source-bound native validation and document bounded support.
 — investment-thesis-monitor

## Unreleased — Phase 1 source fidelity

- Future and unparseable observations never fire. Zero prior EPS produces a not-evaluable percentage revision. Deduplication requires an open thesis alert with the same evidence_fingerprint and escalation; new or changed evidence is re-raised. monitor_run_id binds the complete supplied snapshot. This is an offline calculation, not a scheduled live feed.
- Added detached original-input reconstruction and independent adverse-case regressions. Validation remains draft-only and does not authenticate sources or approvals.


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
  `investment-committee-memo-builder`, `investment-commentary-builder`, `investment-mandate-reviewer`);
  golden Elevated + confirming + dedup + freshness-gap queue; deterministic script checks;
  no-autonomous-action safety + injection; external-delivery authorization.
- **Handoffs:** downstream to `earnings-results-analyzer`, `scenario-sensitivity-generator`,
  `dcf-modeler`, `coverage-initiation-researcher`, `portfolio-performance-attributor`,
  `investment-committee-memo-builder`, `investment-commentary-builder`; sibling monitors
  `investment-mandate-reviewer`, `counterparty-exposure-monitor`; trade/close-thesis/advice to
  the human PM / trading desk / licensed professional.

### Pending before release
- Domain SME (research/investment) + control-owner blind review; precision/recall tuning of
  tolerances against a labeled backtest of real thesis breaks.
- Confirm the versioned tolerance/escalation config source and its owner.
- Wire read-only MCP integrations (thesis register, PMS/OMS, market data, research/estimates,
  config) and the scheduled runner cadence at deployment.
