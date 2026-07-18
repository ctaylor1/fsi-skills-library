# Domain Rules — mandate-compliance-monitor

How the monitor evaluates mandate, guideline, regulatory, concentration, ESG, and
restriction limits and maps results to alert severity. **Every limit is versioned
configuration** owned by the investment-compliance function (`config_version`); limits are
never hard-coded here, never inferred from holdings, and never tuned per-portfolio.
Orientation references: the fund's IPS / mandate documents, applicable diversification rules
(e.g., 1940 Act 5/10/40, UCITS 5/10/40), and the firm's restricted-list policy take
precedence over anything in this file.

## Rule taxonomy

| Rule `type` | Scope | Fires (default config) | Evidence attached |
| ----------- | ----- | ---------------------- | ----------------- |
| `concentration` | `issuer` / `sector` | Bucket market value / NAV **>** `limit_pct` (BREACH); within `warn_buffer_pct` below it (WARN) | Bucket %, market value, rule |
| `regulatory` | `issuer` / `sector` | Same math as concentration, but a **regulatory hard cap** (e.g., diversification limit) | Bucket %, limit, rule |
| `guideline` | `asset_class` | Asset-class weight vs `max_pct` (or `min_pct` for floors like minimum cash) | Class %, limit, rule |
| `restriction` | `security` | A **held** restricted/prohibited security, or a **proposed buy** of one | Security id(s), trade id(s), rule |
| `esg` (`min_score`) | portfolio | Any holding with `esg_score` **<** `min_score` | Offending securities + worst score |
| `esg` (`exclusion`) | portfolio | Any holding in an `excluded_sectors` category (e.g., Controversial Weapons) | Offending securities + sector |

Threshold classification is deterministic:

- **BREACH** when `measured > limit` (max rules) or `measured < limit` (min rules).
- **WARN** when within `warn_buffer_pct` of the limit but not yet over it (early warning).
- **PASS** otherwise (no alert emitted).

## Position vs. pre-trade (`breach_type`)

- `position` — the **current** book of record already breaches the limit. In asset
  management this is often a *passive* breach (caused by market movement) that typically
  carries a cure period; the monitor only reports it and its evidence — it does **not**
  grant, track, or close a cure.
- `pre_trade` — a **proposed / pending order** would newly cause a BREACH (the current
  bucket is not already breached). This is the *active* pre-trade signal that most warrants
  reviewer attention before the order is worked. The monitor flags it; it never blocks,
  cancels, or releases the order.
- `freshness` — the portfolio's positions are older than `max_staleness_days`; raised so the
  reviewer knows results may not reflect the current book.

## Severity mapping (deterministic, documented)

Severity is a triage suggestion, computed from `(rule_type, status, breach_type)` — see
`expected_severity` in `scripts/calculate_or_transform.py` and re-derived in
`scripts/validate_output.py`:

| Severity | Rule / condition | Routed queue |
| -------- | ---------------- | ------------ |
| **High** | Any `restriction` or `regulatory` BREACH, **or** any `pre_trade` BREACH | `compliance-escalation` |
| **Medium** | `concentration` / `guideline` / `esg` **position** BREACH | `compliance-review-queue` |
| **Low** | Any WARN (approaching a limit), **or** a `freshness` flag | `monitoring-watchlist` |

Severity and queue are fully determined by the rule set and the versioned limits; they are
never adjusted by hand for a specific portfolio or manager.

## Deduplication

Each result has a stable `fingerprint` = `portfolio_id|rule_id|bucket|breach_type|status`.
The run compares fingerprints to the `open_alerts` baseline: matches are marked
`is_duplicate` and routed to **still-open** (not re-raised as new); everything else is
**new**. This keeps a persistent breach from re-alerting every scheduled run while still
recording that it remains open.

## Hard boundaries (fail closed)

- **Alert only.** Never block/cancel/release a trade, sell/buy/rebalance/trim a position,
  grant or track a cure or waiver, or close/suppress an alert. Those are human compliance
  and portfolio-management actions.
- **No limit invention or tuning.** Use only the versioned config; if a limit is missing or
  ambiguous, report the gap rather than guessing a threshold.
- **No intent or advice.** Describe a breach factually (measured vs limit); do not assert
  wrongdoing, nor recommend a specific trade, security, or allocation to cure it.
- **No silent staleness.** If positions are stale, flag it; do not present stale results as
  current or drop the portfolio.
