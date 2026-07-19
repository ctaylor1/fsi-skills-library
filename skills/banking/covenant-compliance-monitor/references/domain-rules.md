# Domain Rules — covenant-compliance-monitor

How the monitor evaluates financial, negative, and reporting covenants, reconciles the
borrower compliance certificate, and maps results to alert severity. **Every covenant
definition, threshold, and calculation mechanic is versioned configuration** parsed from the
executed credit agreement (`config_version`), owned by the credit function; nothing here is
hard-coded, inferred from a spread, re-interpreted from legal language, or tuned per-borrower.
Orientation references: the executed credit agreement and its amendments, the bank's approved
spreading taxonomy, and the servicing deliverable schedule take precedence over anything in
this file.

## Covenant taxonomy

| Covenant `type` | Computed from | Fires (per versioned config) | Evidence attached |
| --------------- | ------------- | ---------------------------- | ----------------- |
| `financial` (ratio) | Approved spread line items via `formula` (numerator / `numerator_less` / denominator) | `direction:max` cap **>** `threshold` (BREACH), or `direction:min` floor **<** `threshold` (BREACH); WARN within `cushion` | Metric, measured, threshold, headroom, trend, rule |
| `financial` (level) | A single spread line item (empty denominator), e.g. minimum TNW / minimum EBITDA | Same max/min math on the level value | Level, threshold, headroom, rule |
| `negative` | One spread line item vs a basket cap (e.g. permitted additional indebtedness, restricted payments, capex) | `direction:max` value **>** basket `threshold` (BREACH); WARN within `cushion` | Line item, measured, threshold, headroom, rule |
| `reporting` | Deliverable `due_date` / `received_date` vs run `as_of` | Not received and past `due_date` + `grace_days` → BREACH (overdue); received after the effective due date → WARN (late) | Deliverable, due/received dates, overdue/late days, rule |

Threshold classification is deterministic:

- **BREACH** when `measured > threshold` (max covenants) or `measured < threshold` (min
  covenants).
- **WARN** when within `cushion` of the threshold but not yet over/under it (early warning on
  thin headroom).
- **PASS** otherwise (no alert emitted).

A holding of the value exactly **at** the threshold is WARN, not BREACH — a max covenant
breaches only when strictly over, a min covenant only when strictly under.

## Certificate reconciliation (`breach_type: reconciliation`)

For any financial covenant the borrower reports in the compliance certificate, the monitor
compares its **independently computed** value against the **borrower-reported** value. When
the absolute difference exceeds the covenant's `recon_tolerance` (default 0.05 for ratios,
0.5% of the threshold for levels), it raises a **reconciliation** alert citing both values.
A reconciliation break is a discrepancy to **investigate** — the borrower may have used a
different definition, a different period, or misreported — not, by itself, a confirmed
covenant breach or a finding of misreporting. Both can be true at once (a covenant is breached
**and** the certificate overstated compliance); each is a separate alert.

## Headroom and trend

- **Headroom** = `threshold − measured` (max covenants) or `measured − threshold` (min
  covenants). Positive is compliant room; negative is breach magnitude.
- **Trend** compares the current computed value to the prior period's (when a `prior_spread`
  is supplied) and labels the movement `improving` / `flat` / `deteriorating` in the
  approaching-the-limit direction. Headroom and trend are **descriptive evidence** for the
  reviewer, never a credit determination or a forecast of future compliance.

## Test period vs. reporting deadline (`breach_type`)

- `financial_test` — the current approved spread breaches (or is within cushion of) a
  financial covenant threshold for the test period.
- `negative_covenant` — a basket / restriction cap is exceeded (or approached).
- `reconciliation` — the bank-computed value materially disagrees with the borrower
  certificate.
- `reporting` — a required deliverable (compliance certificate, audited/interim financials) is
  overdue (BREACH) or was delivered late (WARN).
- `freshness` — the approved spread is older than `max_staleness_days`; raised so the reviewer
  knows the tests may not reflect the current financials.

## Severity mapping (deterministic, documented)

Severity is a triage suggestion, computed from `(covenant_type, status, breach_type)` — see
`expected_severity` in `scripts/calculate_or_transform.py` and re-derived in
`scripts/validate_output.py`:

| Severity | Condition | Routed queue |
| -------- | --------- | ------------ |
| **High** | Any `financial_test`, `negative_covenant`, or `reporting` **BREACH** (potential event of default / reporting default) | `credit-risk-escalation` |
| **Medium** | A certificate **reconciliation** break (discrepancy to investigate) | `credit-review-queue` |
| **Low** | Any WARN (thin headroom, late-but-delivered filing), **or** a `freshness` flag | `covenant-monitoring-watchlist` |

Severity and queue are fully determined by the covenant set and the versioned thresholds; they
are never adjusted by hand for a specific borrower or relationship.

## Deduplication

Each result has a stable `fingerprint` = `facility_id|covenant_id|breach_type|status`. The run
compares fingerprints to the `open_alerts` baseline: matches are marked `is_duplicate` and
routed to **still-open** (not re-raised as new); everything else is **new**. This keeps a
persistent breach (e.g., a leverage breach carrying a negotiated cure period) from re-alerting
every scheduled run while still recording that it remains open.

## Hard boundaries (fail closed)

- **Alert only.** Never declare default, accelerate/call/restructure a facility, grant or draft
  a waiver or amendment, issue a reservation of rights, change a risk rating, notify the
  borrower, or close/suppress an alert. Those are human credit and legal actions.
- **No covenant invention, re-interpretation, or tuning.** Use only the versioned covenant
  library; if a definition, mechanic, or threshold is missing or ambiguous, report the gap
  rather than guessing. Ambiguous legal wording is a loan-documentation/counsel question.
- **No intent or advice.** Describe a breach factually (measured vs threshold, headroom,
  trend); do not assert wrongdoing or recommend specific cure/waiver terms.
- **No silent staleness.** If a spread is stale, flag it; do not present stale results as
  current or drop the facility.
