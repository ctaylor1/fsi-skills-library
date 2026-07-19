# Domain Rules — concentration-risk-monitor

How the monitor aggregates exposures and evaluates concentration, absolute-cap, and
diversification-floor limits, and maps results to alert severity. **Every limit is versioned
configuration** owned by the enterprise-risk function (`config_version`); limits are never
hard-coded here, never inferred from exposures, and never tuned per-book. Orientation
references: the firm's risk-appetite statement and concentration-risk policy, applicable
large-exposure rules (e.g., the single-counterparty large-exposure framework), and
operational-resilience / third-party concentration guidance take precedence over anything in
this file.

## Aggregation model

Each book's exposures are aggregated into **buckets** along a **scope** (a dimension field).
The engine is generic over scope — any field present on an exposure may be a scope:
`counterparty`, `counterparty_group`, `sector`, `geography`, `product`, `cloud_provider`,
`ai_provider`, `technology_provider`, `operational_dependency`, or a deployment-specific
field. An exposure that lacks the scope field does not contribute a bucket for that dimension.

A **basis** is a named denominator on the book's `bases` map (e.g. `total_exposure`,
`eligible_capital`). Concentration percentages are `bucket_amount / basis_value * 100`. The
basis is **fixed** for the run — a proposed exposure adds to the bucket numerator but does not
inflate the basis (a conservative forward check).

## Rule taxonomy

| Rule `type` | Scope | Fires (default config) | Evidence attached |
| ----------- | ----- | ---------------------- | ----------------- |
| `concentration` | any dimension | Bucket % of `basis` **>** `limit_pct` (BREACH); within `warn_buffer_pct` below it (WARN). Mark `regulatory: true` for a hard regulatory cap (e.g., single-counterparty large-exposure limit). | Bucket %, amount, basis, top contributors, rule |
| `absolute_cap` | any dimension | Bucket **amount** **>** `limit_amount` (a notional cap); within `warn_buffer_amount` below it (WARN) | Bucket amount, limit, top contributors, rule |
| `diversification` | any dimension | Distinct **populated** buckets in the dimension **<** `min_count` (BREACH) — a single-point dependency / thin-diversification floor | Distinct count, min, buckets present, rule |

Threshold classification (concentration / absolute-cap) is deterministic:

- **BREACH** when `measured > limit` (strictly over).
- **WARN** when within `warn_buffer` of the limit but not yet over it (early warning).
- **PASS** otherwise (no alert emitted).

Diversification is a **floor**: **BREACH** when a book has at least one populated bucket but
fewer distinct buckets than `min_count`; **not applicable** (skipped) when the book has zero
populated buckets in that dimension (no dependency to concentrate).

## Current vs. proposed (`breach_type`)

- `current` — the **current** exposure book already breaches (or warns on) the limit.
- `proposed` — a **proposed / pipeline** exposure (a new facility, onboarding, or workload
  migration) would newly cause a BREACH in a bucket that is **not already** breached. This is
  the forward pre-onboarding signal that most warrants reviewer attention before the exposure
  is booked. The monitor flags it; it never blocks the onboarding.
- `freshness` — the book's exposures are older than `max_staleness_days`; raised so the
  reviewer knows results may not reflect the current book.

## Severity mapping (deterministic, documented)

Severity is a triage suggestion, computed from
`(rule_type, status, breach_type, regulatory)` — see `expected_severity` in
`scripts/calculate_or_transform.py` and re-derived in `scripts/validate_output.py`:

| Severity | Rule / condition | Routed queue |
| -------- | ---------------- | ------------ |
| **High** | Any `proposed` BREACH, **or** any `diversification` BREACH, **or** any `regulatory` concentration BREACH | `risk-escalation` |
| **Medium** | Any non-regulatory `current` `concentration` / `absolute_cap` BREACH | `risk-review-queue` |
| **Low** | Any WARN (approaching a limit), **or** a `freshness` flag | `risk-monitoring-watchlist` |

Severity and queue are fully determined by the rule set and the versioned limits; they are
never adjusted by hand for a specific book, business line, or provider.

## Deduplication

Each result has a stable `fingerprint` = `book_id|rule_id|bucket|breach_type|status`. The run
compares fingerprints to the `open_alerts` baseline: matches are marked `is_duplicate` and
routed to **still-open** (not re-raised as new); everything else is **new**. This keeps a
persistent concentration from re-alerting every scheduled run while still recording that it
remains open.

## Hard boundaries (fail closed) — R3 decision support

- **Alert and recommend only.** Never reduce/exit/hedge an exposure, block an onboarding,
  migrate or terminate a provider, grant or change a limit or waiver, or close/suppress an
  alert. Those are human risk-management actions.
- **No regulated determination.** Never confirm a reportable breach, file a regulatory return,
  attest a control, or close a case. State measured value vs limit factually; a human
  adjudicates.
- **No limit invention or tuning.** Use only the versioned config; if a limit or basis is
  missing or ambiguous, report the gap rather than guessing a threshold.
- **No intent or advice.** Describe a concentration factually (measured vs limit); do not
  assert wrongdoing, nor recommend a specific exposure, hedge, or provider to cure it.
- **No silent staleness.** If exposures are stale, flag it; do not present stale results as
  current or drop the book.
