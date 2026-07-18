# Changelog — post-trade-settlement-monitor

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). A scheduled,
read-only, alert-only settlement-exception monitor for capital-markets settlement operations.

- **Scope:** read clearing/CSD + OMS status for a book of instructions, apply versioned
  thresholds, deduplicate, stamp freshness, prioritize by severity, and package a human alert
  queue with drafted escalation routes. Read-only; no action, decision, closure, or write.
- **Alert rules (deterministic):** `unmatched_near_cutoff`, `cutoff_breach`, `settlement_fail`,
  `fail_aging_high`, `fail_aging_critical`, `buyin_exposure`, `material_cash_impact`,
  `penalty_accrual` — each with a fixed severity and cited evidence (see
  `scripts/calculate_or_transform.py`).
- **Controls:** R2; `read-only-monitoring` scheduled agent; hard boundary against any
  settlement action (match/affirm/cancel/settle/release/buy-in), determination, or closure;
  versioned-config thresholds only; deduplication against open alerts; freshness/staleness
  surfacing; `external-delivery` approval.
- **Scripts:** `validate_input` (snapshot schema, evaluability + dedup/freshness warnings),
  the alert engine, `validate_output` (escalation packaging, deterministic severity tie-out,
  deduplication, freshness consistency, empty `actions_taken` + no-action-language screen,
  disclaimer).
- **Evaluations:** trigger/routing, golden queue vs `settlement_snapshot.json`, no-cutoff
  edge, deterministic script checks, no-autonomous-action safety + injection, external-delivery
  authorization.
- **Handoffs:** downstream to `trade-break-resolver`, `margin-collateral-optimizer`,
  `transaction-reporting-quality-checker`, `corporate-action-election-assistant`,
  `trade-confirmation-explainer`; CSDR buy-in/penalty decisions and counterparty/custodian
  outreach are human operations handoffs, not skills.

### Pending before release
- Domain SME (settlement operations) + control-owner blind review; confirm CSDR/T+1 rule
  parameters against the firm standard.
- Confirm the versioned threshold/severity config source and its owner, and wire the
  deployment market/holiday calendar for business-day aging.
- Wire read-only MCP integrations (clearing/CSD, OMS/EMS, reference data, config, alert queue)
  and the scheduled-run cadence at deployment.
