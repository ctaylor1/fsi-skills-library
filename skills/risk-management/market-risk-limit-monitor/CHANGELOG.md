# Changelog — market-risk-limit-monitor

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). A scheduled, read-only,
alert-only market-risk limit monitor for trading risk management.

- **Scope:** evaluate trading books / desks / firm units against versioned VaR,
  expected-shortfall, sensitivity (DV01/CS01/vega), stress-loss, notional, and concentration
  limits; classify PASS/WARN/BREACH with cited evidence and utilization %; distinguish current
  from pre-deal (projected) breaches; deduplicate against open breaches; check freshness; queue
  severity-ranked exceptions. Read-only; **no autonomous action, decision, limit change, waiver,
  closure, or filing**.
- **Limit engine (deterministic):** metric-to-limit join by unit + metric discriminators
  (horizon/confidence for VaR/ES, sensitivity for Greeks, scenario for stress), max/min
  thresholds with a `warn_buffer_pct` warning line, and a projected pre-deal pass that flags a
  pending exposure which would newly breach — each explainable, evidenced, and reproducible
  (see `scripts/calculate_or_transform.py`). Risk numbers are read from the risk engine, never
  re-derived or aggregated across books.
- **Controls:** R3; scheduled `read-only-monitoring`, alert-only posture; hard boundary against
  trading/hedging/cutting/rebalancing positions, granting/raising/waiving limits or excesses,
  clearing/closing breaches, closing/suppressing alerts, and filing breach/regulatory reports;
  versioned-config thresholds only; `required` human adjudication before any disposition,
  delivery, filing, or system-of-record change.
- **Scripts:** `validate_input` (run/unit/limit schema, evaluability + freshness/dedup
  warnings), the limit engine, and `validate_output` (alert well-formedness, deterministic
  severity/queue tie-out, deduplication integrity, freshness-handling, no-autonomous-action /
  decision / closure / filing screen, disclaimer, escalation tie-out).
- **Evaluations:** trigger/routing, a golden multi-book limit run (breach mix across
  VaR/ES/stress/concentration, near-limit warnings, a pre-deal projected breach, deduplication,
  freshness, and a fully-compliant book), deterministic script checks, a no-autonomous-action
  safety fixture (`expect_exit 1`) plus an injection case, a no-open-baseline edge, and a
  required-adjudication authorization case.
- **Handoffs:** downstream to `portfolio-exposure-analyzer`, `scenario-sensitivity-generator`,
  `stress-test-scenario-designer`, `concentration-risk-monitor`,
  `liquidity-risk-scenario-analyzer`, `counterparty-exposure-monitor`,
  `margin-collateral-optimizer`, `investment-committee-memo-builder`,
  `board-committee-pack-builder`, and `regulatory-change-impact-analyzer`; remediation,
  limit changes, and breach disposition remain human.

### Pending before release
- Domain SME (market risk) + control-owner blind review; model-risk review of the VaR/ES/stress
  inputs and the utilization/warning-line thresholds.
- Confirm the versioned limit-register source, its owner, and the `config_version` contract;
  confirm the risk-engine measures are the book of record and are not re-derived here.
- Wire read-only MCP integrations (risk engine, position/sub-ledger, limit & risk-appetite
  register, scenario library, reference/market data, prior-breach register) at deployment.
- Calibrate `warn_buffer_pct` per limit and `max_staleness_hours` per framework with market
  risk and the risk-appetite function.
