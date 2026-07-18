# Changelog — counterparty-exposure-monitor

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). A scheduled,
read-only, alert-only counterparty-exposure monitor (Monitor & alert archetype;
`aws-fsi-scheduled-agent: read-only-monitoring`).

- **Scope:** aggregate net current exposure per counterparty across settlement, derivative
  MtM (net of collateral + PFE), financing, and deposit lines; evaluate limit utilization,
  single-name concentration, and credit developments (rating floor, negative watch, CDS
  widening) against a versioned limit register; raise alerts to a human queue. Read-only;
  no action, no decision, no closure, no system-of-record write.
- **Aggregation & signals (deterministic):** `max(0, CE − collateral) + PFE` per row summed
  per counterparty; limit-utilization / concentration / credit-development severity mapping
  (Warning/Breach/Critical) with deterministic severity → queue/SLA/escalate-to packaging
  (see `scripts/calculate_or_transform.py`, `references/domain-rules.md`).
- **Controls:** R2; scheduled read-only, alert-only posture; hard boundary against
  collateral/limit/trade/counterparty actions, credit/trading decisions, and alert
  closure/suppression; versioned-config thresholds only; `external-delivery` approval.
- **Scripts:** `validate_input` (exposure/limit/feed schema, freshness + evaluability
  warnings), aggregation/alert engine, `validate_output` (citation + freshness tagging,
  deduplication, escalation packaging, `run_severity` tie-out, no-autonomous-action screen,
  standing disclaimer).
- **Evaluations:** trigger/routing, golden critical-breach case (8 alerts, mixed
  severity/freshness/recurrence), deterministic script checks, stale-feed edge, no-action
  safety + injection, external-delivery authorization.
- **Handoffs:** downstream to `portfolio-exposure-analyzer`, `liquidity-stress-analyzer`,
  `investment-committee-memo-builder`, `mandate-compliance-monitor`; siblings distinguished
  from `investment-thesis-monitor`, `market-risk-limit-monitor`, `concentration-risk-monitor`,
  `post-trade-settlement-monitor`.

### Pending before release
- Domain SME (counterparty-credit-risk) + control-owner blind review.
- Confirm the versioned limit-register source, rating ladder, and threshold owner.
- Wire read-only MCP integrations (PMS/OMS, risk system, market/credit data, reference data,
  limit register) and the append-only review queue at deployment.
