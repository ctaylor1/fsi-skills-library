# Domain Rules — real-time-payment-risk-monitor

How the monitor evaluates instant-payment risk rules and maps results to alert severity.
**Every threshold and watchlist is versioned configuration** owned by the payments-risk /
fraud function (`config_version`); limits are never hard-coded here, never inferred from the
flow, and never tuned per-account. Orientation references: scheme rulebooks (RTP, FedNow,
SEPA Instant, Faster Payments), the firm's transaction-risk and sanctions-screening policies,
and applicable AML/BSA obligations take precedence over anything in this file. Nothing here is
a fraud, AML, mule, or sanctions **determination** — that is human adjudication.

## Rule taxonomy

| Rule `type` | Scope | Fires (default config) | Evidence attached |
| ----------- | ----- | ---------------------- | ----------------- |
| `velocity` (`count`) | sender account | Outbound settled **count** in the window **>** `limit` (BREACH); within `warn_buffer` below it (WARN) | Count, limit, rule |
| `velocity` (`amount`) | sender account | Outbound settled **value** in the window **>** `limit`; WARN within `warn_buffer` | Value, limit, rule |
| `limit` | per transaction | A single outbound payment `amount` **>** `limit` (per-transaction cap); WARN within `warn_buffer` | Offending payment(s), amount, rule |
| `structuring` | sender account | Count of outbound payments in the near-threshold band `[report_threshold*(1-band_pct), report_threshold)` **>=** `min_count` | Offending payments, band, rule |
| `mule` | account | Inbound then outbound **pass-through**: `outbound/inbound >= passthrough_pct` **and** distinct outbound beneficiaries `>= min_beneficiaries` | Inbound/outbound totals, ratio, beneficiaries, rule |
| `watchlist` | counterparty | Any payment whose `counterparty_id` is on the named list (`sanctions` / `fraud` / `mule`) | Offending payment(s), counterparty, list, rule |
| `liquidity` | settlement position | `net_outflow / prefunded_liquidity` **>** `limit_pct`; WARN within `warn_buffer_pct` | Utilization %, prefunded, rule |

Threshold classification is deterministic:

- **BREACH** when `measured > limit` (all rules here are maximum caps).
- **WARN** when within `warn_buffer` of the limit but not yet over it (early warning).
- **PASS** otherwise (no alert emitted). A value exactly at the limit is **WARN**, not BREACH.

`structuring`, `mule`, and `watchlist` are pattern/membership rules that fire directly to
BREACH (no WARN band); freshness fires WARN.

## Flow vs. inflight (`breach_type`)

- `flow` — the observed **settled** activity already crosses the threshold. Instant payments
  are irrevocable, so this is an after-the-fact signal the monitor reports (with evidence) for
  human review; it does **not** reverse, return, or repair the payment.
- `inflight` — a **still-pending** payment (velocity `amount`, per-transaction `limit`,
  watchlist, or `liquidity` with `pending_outflow`) would newly push the entity into BREACH
  (the settled position is not already breaching). This is the most actionable signal for a
  human to review before the payment releases — but the monitor never holds, releases, or
  cancels it. Inflight is only raised when the current settled state is not already a BREACH.
- `freshness` — the entity's feed is older than `max_staleness_minutes`; raised so the
  reviewer knows results may not reflect current flow.

## Severity mapping (deterministic, documented)

Severity is a triage suggestion, computed from `(rule_type, status, breach_type)` — see
`expected_severity` in `scripts/calculate_or_transform.py` and re-derived in
`scripts/validate_output.py`:

| Severity | Rule / condition | Routed queue |
| -------- | ---------------- | ------------ |
| **High** | Any `inflight` BREACH, **or** any `watchlist` / `mule` / `liquidity` BREACH | `payment-risk-escalation` |
| **Medium** | `velocity` / `limit` / `structuring` **flow** BREACH | `payment-risk-review-queue` |
| **Low** | Any WARN (approaching a limit), **or** a `freshness` flag | `monitoring-watchlist` |

Severity and queue are fully determined by the rule set and the versioned thresholds; they are
never adjusted by hand for a specific account, customer, or counterparty.

## Deduplication

Each result has a stable `fingerprint` = `entity_id|rule_id|bucket|breach_type|status`. The
run compares fingerprints to the `open_alerts` baseline: matches are marked `is_duplicate` and
routed to **still-open** (not re-raised as new); everything else is **new**. This keeps a
persistent pattern (e.g., a chronically high-velocity merchant account) from re-alerting every
scheduled run while still recording that it remains open.

## Hard boundaries (fail closed)

- **Alert only.** Never block/hold/release/return/reverse/repair a payment, block/freeze/close
  an account, or close/suppress an alert. Those are human actions in entitled systems.
- **No determination.** Never assert fraud, money laundering, a mule, or a confirmed sanctions
  match; describe measured value vs limit and cited membership factually, and route to the
  adjudicating skill/human.
- **No filing.** Never file a SAR/CTR or any regulatory report; that is a human BSA/AML
  decision.
- **No limit invention or tuning.** Use only the versioned config; if a threshold or watchlist
  is missing or ambiguous, report the gap rather than guessing.
- **No silent staleness.** If a feed is stale, flag it; do not present stale results as current
  or drop the entity.
