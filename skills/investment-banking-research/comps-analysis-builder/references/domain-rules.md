# Domain Rules — comps-analysis-builder

Orientation references: standard trading-comparables (comparable-company analysis) practice and
the firm's research/deal standards. The firm's **versioned peer-selection criteria** and
**multiple-band / freshness config** take precedence and are versioned contracts. This skill
applies the deterministic assembly and calculation rules below; it does not exercise a valuation
judgment or make a recommendation.

## Enterprise-value bridge (deterministic, per company)

```
market_cap        = share_price * diluted_shares
enterprise_value  = market_cap + total_debt + preferred_equity + minority_interest - cash_and_equivalents
```

Every bridge component is cited. The output validator re-derives both `market_cap` and
`enterprise_value` from the stored components; an asserted number that does not reconcile
(beyond a 1-unit rounding tolerance) is treated as an unsupported claim and fails closed.

## Trading multiples

| Multiple | Numerator | Denominator |
| -------- | --------- | ----------- |
| EV/Revenue LTM / FY1 | enterprise value | LTM / forward revenue |
| EV/EBITDA LTM / FY1 | enterprise value | LTM / forward EBITDA |
| EV/EBIT LTM | enterprise value | LTM EBIT |
| P/E LTM | share price | LTM EPS |

Each multiple is classified deterministically:

| Status | Condition | Consequence |
| ------ | --------- | ----------- |
| `meaningful` | Denominator present and `> 0`, value inside the configured band | Used in the summary statistics |
| `nm` | Denominator present but `<= 0` (e.g. negative EBITDA) | Shown as `nm`; excluded from statistics |
| `missing` | Denominator absent | Missing-metric open item; excluded; never fabricated |
| `outlier` | Value outside the configured band for that multiple | Shown, flagged; excluded from statistics; confirm-exclusion open item |

`nm`, `missing`, and `outlier` are **per multiple**, not per company — a loss-making peer can
still be a meaningful EV/Revenue comp while its EV/EBITDA is `nm`.

## Freshness

A company whose `price_date` is older than `max_price_age_days` (default 5) relative to
`as_of_date`, or which has no `price_date`, is marked **stale**. Stale companies are computed and
cited but **excluded from the summary statistics** and raised as a refresh open item.

## Summary statistics

For each multiple, over the meaningful, in-stats peer values (subject excluded; `nm`/`missing`/
`outlier`/stale excluded): `n`, `min`, `Q1`, `median`, `mean`, `Q3`, `max`. Percentiles use
linear interpolation (R-7). If no meaningful values exist, the statistic is `n = 0` and reported
as not-derivable. If the included-peer count is below `min_peers` (default 3), a thin-peer-set
open item is raised.

## Implied valuation (cross-check range only)

For each configured `implied_multiples` metric:

```
implied_ev     = peer_statistic * subject_metric        (statistic = Q1 / median / mean / Q3)
implied_equity = implied_ev - subject_debt - preferred - minority + cash
implied_price  = implied_equity / subject_diluted_shares
```

The result is an **analytical cross-check range** for human review — explicitly **not** a price
target, a recommendation, or a valuation conclusion. Every implied row records its statistic
basis.

## Approvals capture (recorded, never assumed)

- Approvals with `status == "recorded"` are captured with `type`, `approver_role`, `approver`
  (masked), `date`, and `citation`.
- Every entry in `required_approvals` (e.g. `peer-set-review`, `supervisory-analyst-review`)
  with no recorded approval becomes an **outstanding** approval and an open item.
- `human_approval_required_before_delivery` is always `true`.

## Open-items taxonomy

`missing-metric` | `nm-multiple` (informational) | `outlier-multiple` | `stale-market-data` |
`excluded-peer-confirm` | `currency-mismatch` | `thin-peer-set` | `outstanding-approval`. Each
open item names the item, its type, a required human action, and (where a source exists) its
citation.

## Hard boundaries (fail closed)

- No **investment recommendation, rating, or price target**.
- No **valuation or fairness opinion** / definitive "the company is worth X" statement.
- No **fabrication** of metrics, prices, share counts, or estimates.
- No **peer cherry-picking** outside the versioned criteria.
- No **MNPI misuse** or selective disclosure outside the information barrier.
- No **delivery/submission** of the analysis (draft-only).

## Analysis manifest — required contents

`analysis_id`, `as_of_date`, `currency`, `config_version`, `template_version`,
`build_status: draft-comps`, `human_approval_required_before_delivery: true`, the canonical
`sections` (analysis summary, subject company, peer set, EV bridges, trading multiples, summary
statistics, implied valuation, QA checks, open items, approvals, source index), the open-items
list, and the standing note:

> Draft comparable-company analysis for human review only. It is not investment advice, not a
> research rating or price-target, and not a valuation or fairness view; the multiples and any
> implied ranges are an analytical cross-check, and this draft has not been reviewed, approved,
> or delivered.
