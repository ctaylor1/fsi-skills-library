# Changelog — mandate-compliance-monitor

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). A scheduled,
read-only, alert-only mandate-compliance monitor for asset management.

- **Scope:** evaluate portfolios and proposed trades against versioned mandate, guideline,
  regulatory, concentration, ESG, and restriction rules; classify PASS/WARN/BREACH with
  cited evidence; deduplicate against open alerts; check freshness; queue severity-ranked
  exceptions. Read-only; **no autonomous action, decision, cure, or closure**.
- **Rule engine (deterministic):** issuer/sector concentration and regulatory caps,
  asset-class guidelines (max/min), restricted-list (held + pre-trade), and ESG
  minimum-score / sector-exclusion — each explainable, evidenced, and reproducible (see
  `scripts/calculate_or_transform.py`). Position vs. pre-trade `breach_type` distinguishes
  passive market-driven breaches from a proposed order that would newly breach.
- **Controls:** R2; scheduled `read-only-monitoring`, alert-only posture; hard boundary
  against blocking/releasing trades, rebalancing/trimming positions, granting/closing
  cures or waivers, and closing/suppressing alerts; versioned-config thresholds only;
  `external-delivery` approval before delivery or system-of-record change.
- **Scripts:** `validate_input` (run/portfolio/rule schema, evaluability + freshness/dedup
  warnings), the rule engine, and `validate_output` (alert well-formedness, deterministic
  severity/queue tie-out, deduplication integrity, freshness-handling, no-autonomous-action
  screen, disclaimer, escalation tie-out).
- **Evaluations:** trigger/routing, a golden multi-portfolio exception run (breach mix,
  pre-trade breach, deduplication, freshness, and a fully-compliant portfolio), deterministic
  script checks, a no-autonomous-action safety fixture (`expect_exit 1`) plus an injection
  case, a no-open-baseline edge, and external-delivery authorization.
- **Handoffs:** downstream to `portfolio-exposure-analyzer`, `liquidity-stress-analyzer`,
  `counterparty-exposure-monitor`, `portfolio-rebalancing-assistant`,
  `best-execution-reviewer`, `investment-committee-memo-builder`, and
  `regulatory-change-impact-analyzer`; remediation and disposition remain human.

### Pending before release
- Domain SME (investment compliance) + control-owner blind review; fairness/ESG-methodology
  review of exclusion and scoring inputs.
- Confirm the versioned rule-library source, its owner, and the `config_version` contract.
- Wire read-only MCP integrations (PMS/OMS positions & proposed trades, rule library,
  reference/market data, restricted list, prior-alert store) at deployment.
- Calibrate `warn_buffer_pct` and `max_staleness_days` per mandate with compliance.
