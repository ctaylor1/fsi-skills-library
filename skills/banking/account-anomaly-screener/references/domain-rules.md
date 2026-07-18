# Domain Rules — account-anomaly-screener

Explainable anomaly **signals** and how they map to a **review-priority band**. Thresholds
are configuration (versioned, owned by the fraud-strategy team), not hard-coded judgments,
and never tuned to an individual. Orientation reference: 2026 FINRA report (cyber-enabled
fraud) and the firm's fraud-strategy standard take precedence.

## Signal taxonomy

| Signal | Fires when (default config) | Evidence attached |
| ------ | --------------------------- | ----------------- |
| `amount_vs_history` | Focal debit amount > baseline mean + `k`·stdev (default k=3) of same-direction, same-channel activity | Focal txn + baseline stats + window |
| `velocity` | Count of transactions in a rolling window exceeds `velocity_max` (default 10 / 1h) | The burst rows + timestamps |
| `new_counterparty_high_value` | First-seen payee/merchant AND amount ≥ `new_payee_amount` (default 1,000) | Payee first-seen + amount |
| `geo_novelty` | Transaction country/region not seen in lookback AND no CRM travel notice | Location + prior geo set + CRM notice status |
| `channel_novelty` | Channel (e.g., wire, crypto on-ramp) not previously used by the account | Channel + prior channel set |
| `dormancy_reactivation` | Account inactive ≥ `dormancy_days` (default 120) then a debit ≥ `reactivation_amount` | Last-active date + focal txn |
| `round_amount_clustering` | ≥ `cluster_count` (default 3) round-number debits just under a reporting threshold within `cluster_days` | The clustered rows (factual only) |
| `rapid_in_out` | Large credit followed by near-equal debit(s) within `passthrough_hours` (default 48) | Credit + matching debits |

Signals are **additive and independent**; the output reports each that fired with its own
evidence. There is no opaque composite "fraud score".

## Priority mapping (deterministic, documented)

| Suggested band | Rule |
| -------------- | ---- |
| **Informational** | 0 signals fired, or only low-weight novelty signals with benign CRM context |
| **Review** | 1–2 signals fired without an obvious benign explanation |
| **Elevated** | ≥ 3 signals fired, OR any of `rapid_in_out` / `round_amount_clustering` fired |

Priority is a **triage suggestion for a human reviewer**. It is not a fraud determination
and it never triggers an account action.

## Hard boundaries (fail closed)

- Never state or imply that activity **is** fraud, money laundering, or "structuring to
  evade" — describe patterns factually and attribute conclusions to the human reviewer.
- Never recommend or take an **account action** (block, freeze, hold, close, reverse).
- Never tune thresholds to the individual or infer "what's normal for this person" beyond
  the computed baseline.
- `round_amount_clustering` and `rapid_in_out` describe **patterns**, not intent.

## Benign-explanation prompts (always include when relevant)

Payroll/benefit changes, tax refunds, seasonal spending, a genuine large purchase, a move
or travel (check CRM travel notice), a new recurring biller, account holder using a new
device/branch. The pack must invite the reviewer to weigh these.
