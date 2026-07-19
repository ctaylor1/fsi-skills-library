# Changelog — concentration-risk-monitor

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). A scheduled,
read-only, alert-only concentration-risk monitor for enterprise / credit / operational risk.

- **Scope:** aggregate each book's exposures into buckets along any dimension (counterparty /
  counterparty group, sector, geography, product, cloud / AI / technology provider,
  operational dependency); evaluate against versioned concentration (% of a named basis),
  absolute-cap (notional), and diversification-floor (minimum distinct providers) limits;
  classify PASS/WARN/BREACH with cited evidence; project proposed exposures for a forward
  pre-onboarding breach; deduplicate against open alerts; check freshness; queue
  severity-ranked exceptions. Read-only; **no autonomous action, decision, closure, or
  filing** (R3 decision support).
- **Engine (deterministic):** generic scope aggregation with per-book named bases,
  strictly-over BREACH / within-buffer WARN classification, `current` vs `proposed`
  breach types, a diversification floor (not-applicable when a dimension is unpopulated), and
  a `regulatory` flag that escalates hard regulatory caps — each explainable, evidenced, and
  reproducible (see `scripts/calculate_or_transform.py`).
- **Controls:** R3; scheduled `read-only-monitoring`, alert-only posture; hard boundary
  against reducing/exiting/hedging exposures, blocking/approving onboarding, migrating or
  terminating providers, granting/changing/waiving limits, confirming breaches, filing
  regulatory returns, and closing/suppressing alerts; versioned-config thresholds only;
  `required` human adjudication before any regulated decision or system-of-record write.
- **Scripts:** `validate_input` (run/book/exposure/rule schema, evaluability + freshness/dedup
  warnings), the concentration engine, and `validate_output` (alert well-formedness,
  deterministic severity/queue tie-out, deduplication integrity, freshness-handling,
  no-autonomous-action-or-decision screen, disclaimer, escalation tie-out).
- **Evaluations:** trigger/routing, a golden multi-book concentration run (single-name /
  sector / geography / product / absolute-cap breaches, a proposed pre-onboarding breach, a
  cloud single-point diversification breach, deduplication, freshness, and a fully-compliant
  book), deterministic script checks, a no-autonomous-action/decision safety fixture
  (`expect_exit 1`) plus an injection case, a no-open-baseline edge, and a human-adjudication
  authorization case.
- **Handoffs:** downstream to `third-party-risk-assessor`, `credit-risk-portfolio-analyzer`,
  `operational-risk-event-analyzer`, `stress-test-scenario-designer`,
  `liquidity-risk-scenario-analyzer`, `market-risk-limit-monitor`,
  `key-risk-indicator-monitor`, `enterprise-risk-assessment-builder`, and
  `risk-control-self-assessment-assistant`; assessment, adjudication, and remediation remain
  human.

### Pending before release
- Domain SME (enterprise / credit / operational risk) + control-owner blind review;
  large-exposure and operational-resilience methodology review of bases and diversification
  floors.
- Confirm the versioned limit-library source, its owner, and the `config_version` contract,
  including which limits are `regulatory` hard caps.
- Wire read-only MCP integrations (limit library, exposure/finance data, proposed-exposure
  pipeline, third-party/operational-dependency inventory, reference data, loss-event/scenario
  store, prior-alert store) at deployment.
- Calibrate `warn_buffer_pct` / `warn_buffer_amount`, `min_count` floors, and
  `max_staleness_days` per book and dimension with enterprise risk.
