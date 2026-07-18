# Domain Rules — bank-statement-analyzer

Deterministic, explainable extraction and calculation rules. Categorization keywords and
thresholds are **configuration** (versioned, owned by banking product & credit operations),
not hard-coded judgments, and are never tuned to an individual. Every figure is cited to the
statement line(s) it derives from.

## Extracted metrics

| Metric | Rule (default config) | Evidence attached |
| ------ | --------------------- | ----------------- |
| `income_summary` | Credits whose `category` matches `income_categories` (payroll, salary, direct-deposit, pension, benefit) OR that recur from the same counterparty ≥ `recurring_min_occurrences` times. Reports total, count, monthly average (total ÷ months in period), and per-source rows. | The income credit rows + period |
| `recurring_obligations` | Debits grouped by normalized counterparty appearing ≥ `recurring_min_occurrences` times whose amounts are stable (every occurrence within `recurring_amount_tol_pct` of the group mean). Distinguishes fixed commitments (rent, loan, subscription) from variable spend. | The obligation rows per counterparty + mean/total |
| `cash_flow` | `total_credits`, `total_debits`, `net_cash_flow = total_credits − total_debits`; per-month net; if opening/closing balances supplied, a tie-out `opening + net == closing`. | Aggregates + monthly rollup |
| `fees` | Debits whose `category == "fee"` or whose counterparty/description matches `fee_keywords` (overdraft, NSF, service charge, maintenance, returned item, ATM fee). Reports total and count. | The fee rows |

## Anomaly flags (factual, evidenced, with confidence)

| Anomaly | Fires when (default config) | Note |
| ------- | --------------------------- | ---- |
| `negative_balance_day` | A row's running `balance` < `low_balance_threshold` (default 0) | Requires balances on rows |
| `nsf_returned_item` | A row matches `nsf`/`returned item`/`insufficient funds` | Factual event, not a judgment |
| `large_one_off_debit` | A non-recurring, non-fee debit > baseline mean + `large_debit_k`·stdev (default k=3) of non-recurring debits | Low-confidence on thin baseline |
| `duplicate_transaction` | Two debits with equal amount + same counterparty within `duplicate_window_hours` (default 24) | Possible double-post; verify |

Anomaly flags are **factual observations**, not fraud findings. For fraud/unusual-activity
screening with a review-priority band, route to `account-anomaly-screener`.

## Confidence flags (always include when relevant)

- Uncategorized-transaction ratio (categorization used keyword heuristics).
- Missing running balances (balance-based anomalies / average balance not evaluable).
- Partial period coverage or a gap in transaction dates.
- Thin baseline (< `min_baseline_n` non-recurring debits) — `large_one_off_debit` is
  low-confidence.
- Statement (document) vs ledger discrepancy.

## Hard boundaries (fail closed)

- Never make or imply a **lending / credit / affordability / eligibility** decision — extract
  and calculate; a human (or `loan-affordability-precheck` for an indicative estimate) decides.
- Never give **personalized financial, investment, or tax advice** or recommend an action.
- Never assert **fraud, intent, or wrongdoing** — describe patterns factually.
- Never tune thresholds or categorization to the individual; use only the versioned config.
