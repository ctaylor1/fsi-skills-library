# Domain Rules — performance-attribution-builder

Orientation references: standard Brinson-Fachler performance attribution and the firm's
performance-measurement standards; SEC Marketing Rule (Rule 206(4)-1) for any advertised
performance and the GIPS standards for composite presentation. The firm's **versioned attribution
config** (model, tolerances, template) and its performance-measurement policy take precedence and
are versioned contracts. This skill applies the deterministic decomposition below; it does not
exercise an investment judgment, make a recommendation, or claim GIPS compliance.

## Model — arithmetic Brinson-Fachler (single period)

All returns are **arithmetic (additive)** for the single period; a segment's base-currency return
is its local return plus its currency return. For each segment `i` (portfolio weight `wp`,
benchmark weight `wb`, local portfolio return `Rlp`, local benchmark return `Rlb`, currency return
`f`), with `Rb_local = sum(wb_i * Rlb_i)`:

```
allocation_i  = (wp_i - wb_i) * (Rlb_i - Rb_local)
selection_i   =  wb_i         * (Rlp_i - Rlb_i)
interaction_i = (wp_i - wb_i) * (Rlp_i - Rlb_i)
currency_i    = (wp_i - wb_i) *  f_i
total_i       = allocation_i + selection_i + interaction_i + currency_i
```

Because the returns are additive, the four effects sum **exactly** to the active return:

```
sum_i(total_i) = Rp - Rb   where   Rp = sum(wp_i * (Rlp_i + f_i)),  Rb = sum(wb_i * (Rlb_i + f_i))
```

The output validator re-derives each segment total from its four components and re-derives the
effect totals; an asserted number that does not reconcile (beyond a `1e-6` tolerance) is treated as
an unsupported claim and fails closed.

## Effects and dimensions (catalog scope)

| Effect / dimension | Definition | Notes |
| ------------------ | ---------- | ----- |
| **Allocation** | over/underweight a segment vs its benchmark-relative return | Brinson-Fachler (uses `Rlb - Rb_local`) |
| **Selection** | in-segment security selection vs the segment benchmark | `wb * (Rlp - Rlb)` |
| **Interaction** | joint weight x selection term | reported separately (not folded into selection) |
| **Currency** | active weight x period currency return | arithmetic currency effect |
| **Instrument** | attribution at instrument-level segmentation | supported by segmenting at instrument granularity |
| **Benchmark** | reconciliation of the bottom-up return to the official benchmark | tie-out, not an effect |

**Factor-based** attribution and **multi-period geometric linking** are out of scope for this
deterministic engine and route to the quant / performance-measurement team (see
[handoffs.md](handoffs.md)).

## Reconciliation (reconcile totals)

1. **Effects tie-out** — `allocation + selection + interaction + currency` must equal the active
   return within `reconciliation_tolerance` (default `1e-6`); otherwise a residual is reported and
   an `unreconciled-effects` open item is raised.
2. **Book-of-record tie-out** — the bottom-up portfolio and benchmark returns are reconciled to the
   official `official_returns` within `official_tolerance` (default `5bps`); a difference beyond
   tolerance is an `official-return-break` open item, never silently accepted.
3. **Weight coverage** — `sum(weight_port)` and `sum(weight_bench)` are checked against `~1.0`
   within `weight_tolerance` (default `0.5%`); any segment missing returns is `needs-data` and its
   weight is reported as `unattributed_weight_port`.

## Freshness / period basis

The attribution is for a single closed period; returns must be final/official for that period (not
intraperiod estimates) and on a consistent classification basis across portfolio and benchmark.

## Approvals capture (recorded, never assumed)

- Approvals with `status == "recorded"` are captured with `type`, `approver_role`, `approver`
  (masked), `date`, and `citation`.
- Every entry in `required_approvals` (e.g. `performance-methodology-review`,
  `compliance-marketing-review`) with no recorded approval becomes an **outstanding** approval and
  an open item.
- `human_approval_required_before_delivery` is always `true`.

## Open-items taxonomy

`missing-return` | `currency-return-zero` | `unreconciled-effects` | `official-return-break` |
`no-official-return` | `weight-sum` | `outstanding-approval`. Each open item names the item, its
type, a required human action, and (where a source exists) its citation.

## Hard boundaries (fail closed)

- No **investment recommendation or advice**; no **suitability** statement.
- No **forward-looking or guaranteed-performance** claim (ex-post only).
- No **GIPS-compliance** assertion (a firm-wide, independently verified claim).
- No **unsubstantiated marketing** superlatives.
- No **fabrication** of returns, weights, or FX rates.
- No **delivery / submission** of the analysis (draft-only).

## Analysis manifest — required contents

`attribution_id`, `period`, `base_currency`, `config_version`, `template_version`,
`build_status: draft-attribution`, `human_approval_required_before_delivery: true`, the canonical
`sections` (attribution summary, portfolio/benchmark, segment attribution, effect totals, currency
attribution, reconciliation, methodology, QA checks, open items, approvals, source index), the
open-items list, and the standing note:

> Draft performance-attribution analysis for human review only. It is not investment advice and not
> a recommendation; it makes no forward-looking or guaranteed-performance claim and asserts no GIPS
> compliance; the effects are an ex-post decomposition of realized return, and this draft has not
> been reviewed, approved, or delivered.
