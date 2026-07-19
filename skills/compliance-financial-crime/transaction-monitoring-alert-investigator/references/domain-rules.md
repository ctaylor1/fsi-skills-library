# Domain Rules — transaction-monitoring-alert-investigator

How the monitor evaluates AML transaction-monitoring typologies for an **escalated** alert and
maps results to indicator severity and a recommended disposition. **Every threshold is
versioned configuration** owned by the financial-crime / FIU function (`config_version`);
thresholds are never hard-coded here, never inferred from the data, and never tuned per
subject or per investigator. Orientation references — the BSA/AML program, the firm's
transaction-monitoring scenario library, FATF/FinCEN typology guidance, and the applicable
SAR-filing standard — take precedence over anything in this file. Nothing here is a finding of
intent or a determination of suspicion.

## Typology taxonomy

| Rule `type` | Fires (default config) | Evidence attached |
| ----------- | ---------------------- | ----------------- |
| `structuring` | `min_count`+ cash **in** deposits each in `[threshold_amount*(1-band_pct), threshold_amount)` within `window_days` (BREACH); `warn_count`+ (WARN) | The candidate cash deposits (id, amount, date) + rule |
| `pass_through` | `total_out / total_in` ≥ `min_ratio_pct` when `total_in` ≥ `min_inflow` (rapid movement of funds through the account) | Inflow / outflow totals, pass-through % + rule |
| `geography` | High-risk-jurisdiction amount / total amount **>** `limit_pct` (`high_risk_countries` list) | High-risk transactions (id, amount, country, counterparty) + exposure % + rule |
| `velocity` | Observed transaction count **>** `expected_period_txns × multiplier` (activity spike vs the customer's profile) | Observed vs baseline count + rule |
| `cash_intensity` | Cash-instrument amount / total amount **>** `limit_pct` | Cash amount, total amount, cash % + rule |
| `freshness` | Subject data older than `max_staleness_days` | Subject data_as_of + staleness + citation |

Threshold classification is deterministic:

- **BREACH** when the measured value crosses the configured threshold (see each row above).
- **WARN** when within `warn_buffer_pct` / `warn_count` of the threshold but not yet over it.
- **PASS** otherwise (no indicator emitted).

These indicators are **risk signals for a human investigator**, not conclusions. A BREACH means
"this pattern crossed a configured typology threshold and warrants human review," never "this is
money laundering" or "file a SAR."

## Indicator severity mapping (deterministic, documented)

Severity is a triage suggestion computed from `(rule_type, status)` — see `expected_severity`
in `scripts/calculate_or_transform.py`, re-derived in `scripts/validate_output.py`:

| Severity | Rule / condition | Routed queue |
| -------- | ---------------- | ------------ |
| **High** | Any `structuring` or `pass_through` BREACH | `fiu-escalation-queue` |
| **Medium** | Any `geography` / `velocity` / `cash_intensity` BREACH | `aml-investigation-queue` |
| **Low** | Any WARN (approaching a threshold) **or** a `freshness` flag | `aml-monitoring-watchlist` |

Severity and queue are fully determined by the rule set and versioned thresholds; they are never
adjusted by hand for a specific subject, alert, or investigator.

## Recommended disposition (deterministic, recommend-only)

Each subject package carries a `recommended_disposition` computed from its indicator tallies —
see `expected_recommendation`, re-derived in `validate_output.py`. `high`/`medium` are BREACH
severity counts; `warn` is the count of non-freshness WARN indicators:

| Recommendation | Condition |
| -------------- | --------- |
| `recommend_escalate` | `high ≥ 1` **or** `medium ≥ 2` |
| `recommend_further_review` | `medium ≥ 1` **or** `warn ≥ 1` |
| `recommend_monitor` | otherwise (no material indicator) |

The vocabulary is **recommend-only** and closed to exactly these three values. A recommendation
is a triage suggestion for a human FIU adjudicator; it is **never** a case closure, an alert
disposition, a "no further action" determination, or a SAR-filing decision. `validate_output`
fails closed if any other disposition value appears, or if the reported value does not tie out to
this mapping.

## Chronology and entity resolution

Each subject package includes a `chronology`: its transactions in non-decreasing `(date, txn_id)`
order, each citing the underlying transaction and resolved counterparty. The chronology is the
spine of the evidence bundle and must remain ordered (checked in `validate_output`). Counterparty
identifiers resolve through the shared entity-resolution service; this monitor never fuzzy-merges
identities on its own authority.

## Deduplication

Each indicator has a stable `fingerprint` = `subject_id|rule_id|bucket|status`. The run compares
fingerprints to the `open_cases` baseline: matches are marked `is_duplicate` and routed to
**still_open** (not re-raised as new); everything else is **new**. This keeps a persistent
pattern on an already-open case from re-alerting every scheduled run while still recording that it
remains open.

## Hard boundaries (fail closed)

- **Alert and recommend only.** Never close a case, disposition/clear an alert, decide or file a
  SAR, freeze/block/exit an account or customer, or write any system of record. Those are human
  FIU decisions.
- **No determination of suspicion or intent.** Describe a crossed threshold factually (measured
  vs threshold); do not assert money laundering, wrongdoing, or "not suspicious."
- **No threshold invention or tuning.** Use only the versioned config; if a threshold is missing
  or ambiguous, report the gap rather than guessing.
- **No silent staleness.** If subject data is stale, flag it; do not present stale results as
  current or drop the subject.
- **Tipping-off / SAR confidentiality.** Never expose SAR existence or investigative content to
  the customer or to unauthorized recipients; route only to entitled FIU queues.
