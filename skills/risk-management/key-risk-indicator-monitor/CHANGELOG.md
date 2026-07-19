# Changelog — key-risk-indicator-monitor

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). A scheduled, read-only,
alert-only Key Risk Indicator (KRI) monitor for enterprise risk management.

- **Scope:** evaluate KRIs against versioned appetite/amber/red thresholds across five lenses —
  threshold band, adverse trend, seasonal-expectation deviation, data quality, and freshness;
  classify PASS/WARN/BREACH with cited evidence and linked incidents; deduplicate against open
  alerts; check freshness; queue severity-ranked exceptions with escalation commentary.
  Read-only; **no autonomous action, decision, waiver, rating change, filing, or closure**.
- **Rule engine (deterministic):** direction-aware threshold classification
  (`higher_is_worse` / `lower_is_worse`), consecutive-adverse-move trend detection (early
  warning, suppressed once red), seasonal-baseline deviation, null/out-of-range data-quality
  detection, and staleness — each explainable, evidenced, and reproducible (see
  `scripts/calculate_or_transform.py`). Boundary convention: a value exactly on the red limit is
  an at-limit WARN, not a BREACH.
- **Controls:** R3 — regulated / control decision support; scheduled `read-only-monitoring`,
  alert-only posture; hard boundary against accepting a risk, granting/tracking a waiver,
  changing a limit/threshold/appetite, changing a risk or control rating, declaring an appetite
  breach, filing a report, or opening/closing/suppressing an alert, incident, or case;
  versioned-config thresholds only; `required` human adjudication before any decision or
  system-of-record change.
- **Scripts:** `validate_input` (run/KRI schema, direction/threshold/observation checks,
  freshness/dedup/data-quality warnings), the rule engine (with a bundled invariant self-test),
  and `validate_output` (alert well-formedness, deterministic severity/queue tie-out,
  deduplication integrity, freshness-handling, no-autonomous-action screen, disclaimer,
  escalation tie-out).
- **Evaluations:** trigger/routing, a golden multi-KRI exception run (threshold breach mix,
  trend, seasonal, data-quality, freshness, deduplication, and a fully-in-appetite KRI),
  deterministic script checks, a no-autonomous-action safety fixture (`expect_exit 1`) plus an
  injection case, a no-open-baseline edge, and required-adjudication authorization.
- **Handoffs:** downstream to `operational-risk-event-analyzer`, `credit-risk-portfolio-analyzer`,
  `liquidity-risk-scenario-analyzer`, `third-party-risk-assessor`, `stress-test-scenario-designer`,
  `enterprise-risk-assessment-builder`, `risk-control-self-assessment-assistant`, and
  `regulatory-change-impact-analyzer`; disposition and adjudication remain human.

### Pending before release
- Domain SME (enterprise risk / control officer) + control-owner blind review; methodology
  review of the trend and seasonal lenses and the criticality-driven severity mapping.
- Confirm the versioned KRI threshold library source, its owner, and the `config_version`
  contract, and the loss-event/incident linkage source.
- Wire read-only MCP integrations (KRI/register library, metric/observation feed, incident
  store, scenario library, third-party inventory, prior-alert store) at deployment.
- Calibrate `max_staleness_days`, `trend_min_moves`, `seasonal_tolerance_pct`, and per-KRI
  `plausible_range` with risk owners.
