# Changelog — real-time-payment-risk-monitor

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). A scheduled,
read-only, alert-only real-time / instant-payment risk monitor for payments-risk and fraud
operations (R3 decision support).

- **Scope:** evaluate windowed instant-payment flows (per sending account) and settlement
  funding positions against versioned velocity, per-transaction limit, structuring, mule
  pass-through, watchlist / sanctions-screening, and prefunded-liquidity rules; classify
  PASS/WARN/BREACH with cited evidence; deduplicate against open alerts; check feed freshness;
  queue severity-ranked alerts. Read-only; **no autonomous action, decision, filing, or
  closure**.
- **Rule engine (deterministic):** outbound velocity (count and amount), per-transaction cap,
  near-threshold structuring, inbound→outbound mule pass-through (fan-out), watchlist /
  sanctions counterparty screening, and settlement prefunded-liquidity utilization — each
  explainable, evidenced, and reproducible (see `scripts/calculate_or_transform.py`). A
  `flow` vs `inflight` `breach_type` distinguishes irrevocable settled activity from a
  still-pending payment that would newly breach (surfaced for human review, never held or
  released).
- **Controls:** R3; scheduled `read-only-monitoring`, alert-only posture; hard boundary
  against blocking/holding/releasing/returning/reversing/repairing payments,
  blocking/freezing/closing accounts, making fraud/AML/mule/sanctions determinations, filing
  SARs/regulatory reports, and closing/suppressing alerts or cases; versioned-config
  thresholds and watchlists only; `required` human adjudication before any decision, action,
  filing, closure, or system-of-record write.
- **Scripts:** `validate_input` (run/account/position/rule schema, evaluability + freshness /
  dedup / watchlist warnings), the rule engine, and `validate_output` (alert well-formedness,
  deterministic severity/queue tie-out, deduplication integrity, freshness handling,
  no-autonomous-action / decision / filing / closure screen, disclaimer, escalation tie-out).
- **Evaluations:** trigger/routing, a golden multi-account run (velocity, inflight limit /
  amount, mule pass-through, sanctions watchlist, structuring, WARN, a stale feed, a clean
  account, and a settlement-liquidity WARN + inflight breach; 11 alerts, 8 breach, 1
  deduplicated), deterministic script checks, a no-autonomous-action safety fixture
  (`expect_exit 1`) plus an injection case, a no-open-baseline edge, and human-adjudication
  authorization.
- **Handoffs:** downstream to `payment-fraud-case-investigator`, `aml-alert-triager`,
  `transaction-monitoring-alert-investigator`, `sanctions-match-adjudicator`,
  `liquidity-risk-scenario-analyzer`, `payment-exception-investigator`,
  `payment-failure-diagnoser`, `iso-20022-message-interpreter`, and
  `payment-repair-assistant`; investigation, adjudication, decision, and disposition remain
  human.

### Pending before release
- Domain SME (payments risk / fraud / BSA-AML) + control-owner blind review; model-risk review
  of velocity / mule / structuring thresholds for precision and recall.
- Confirm the versioned rule-library and watchlist sources, their owners, and the
  `config_version` contract.
- Wire read-only MCP integrations (gateway/processor/acquirer, fraud platform, settlement,
  network rules, ISO 20022 parser, ledger, prior-alert store, case management) at deployment.
- Calibrate velocity / limit / structuring / mule / liquidity thresholds and
  `max_staleness_minutes` per scheme and jurisdiction with payments risk.
