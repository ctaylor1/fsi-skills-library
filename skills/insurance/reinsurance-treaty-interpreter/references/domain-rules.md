# Domain Rules — reinsurance-treaty-interpreter

The rules and arithmetic this skill applies when interpreting an excess-of-loss reinsurance
treaty and illustrating a ceded recovery. These are **descriptive**: they identify and
reproduce what the treaty already specifies. They never determine whether a real claim is
recoverable, nor grade, reserve, or advise (see [controls.md](controls.md)). US default;
configure jurisdiction packs per deployment.

## Treaty terms to identify and interpret

| Term | Plain-language meaning |
| ---- | ---------------------- |
| Attachment / retention | The point above which the layer responds; the cedent keeps losses below it |
| Per-occurrence limit | The most the reinsurer pays for any single occurrence (written "limit xs attachment", e.g. "10 xs 5") |
| Reinstatements | How many times the eroded per-occurrence limit is restored during the period, and the reinstatement premium for each |
| Aggregate limit | The most the reinsurer pays for the whole period = `limit × (1 + reinstatements)` unless a separate aggregate is stated |
| Exclusions | Perils or losses the layer does not cover (e.g. war, terrorism, nuclear); excluded losses do not attach or erode the limit |
| Occurrence / hours clause | How multiple events aggregate into one "occurrence" (e.g. a 72-hour clause for windstorm) |
| Reporting / notice | The cedent's duty to notify losses and provide bordereaux, and the thresholds and timeframes for doing so |
| Reinstatement premium | Additional premium to restore limit, commonly "pro rata as to amount, 100% as to time" |

## Canonical recovery illustration (deterministic)

Implemented in `scripts/calculate_or_transform.py` and re-checked by
`scripts/validate_output.py`. Losses are applied **in order**; the layer erodes as it responds.

```
aggregate_limit          = layer.aggregate_limit  (or limit × (1 + reinstatements))
per occurrence, in order:
  layer_loss             = min(max(gross_loss − attachment, 0), limit)
  remaining_aggregate    = aggregate_limit − cumulative_ceded (before this occurrence)
  ceded_recovery         = min(layer_loss, remaining_aggregate)
  cumulative_ceded      += ceded_recovery
  remaining_aggregate    = aggregate_limit − cumulative_ceded (after)
```

- **Attachment first**: only the part of each occurrence above the attachment enters the layer;
  a loss at or below the attachment recovers **0** (shown, not dropped).
- **Per-occurrence cap**: a single occurrence never recovers more than the per-occurrence `limit`.
- **Aggregate cap**: cumulative ceded never exceeds `aggregate_limit`; once exhausted, further
  occurrences recover 0.

### Reinstatement premium (band method)

The **first** full `limit` of cumulative ceded is covered by the deposit premium (no
reinstatement premium). Each reinstatement `k` (k = 1..reinstatements) covers the cumulative
band `[limit × k, limit × (k + 1)]` and carries a premium percentage `reinstatement_terms[k−1]`
(default 100%). For each occurrence, the reinstated amount is the overlap of its cumulative
range with the reinstatement bands, and:

```
reinstatement_premium(occurrence) =
   Σ over bands touched (  band_amount / limit  ×  premium_pct[band]  ×  layer_premium  )
```

This is "pro rata as to amount": reinstating 70% of the limit at a 100% reinstatement premium
costs 70% of the layer premium. (Pro-rata-as-to-time factors are configured per deployment and
default to 100%.) A one-currency-unit tolerance applies; a miss **fails closed** for re-check.

## Worked example (matches the bundled fixture)

Layer **10,000,000 xs 5,000,000**, one reinstatement at 100%, layer premium 2,000,000,
aggregate limit 20,000,000. Occurrences in order: O-1 gross 12,000,000; O-2 gross 18,000,000;
O-3 gross 3,000,000.

| Occ | Gross | Layer loss | Ceded | Cumulative | Remaining agg | Reinstated | Reinst. premium |
| --- | ----- | ---------- | ----- | ---------- | ------------- | ---------- | --------------- |
| O-1 | 12,000,000 | 7,000,000 | 7,000,000 | 7,000,000 | 13,000,000 | 0 | 0 |
| O-2 | 18,000,000 | 10,000,000 | 10,000,000 | 17,000,000 | 3,000,000 | 7,000,000 | 1,400,000 |
| O-3 | 3,000,000 | 0 | 0 | 17,000,000 | 3,000,000 | 0 | 0 |

Totals: ceded **17,000,000**; reinstatement premium **1,400,000**. O-2 reinstates 7,000,000 of
limit (the cumulative band from 10,000,000 to 17,000,000), so its reinstatement premium is
`7,000,000 / 10,000,000 × 100% × 2,000,000 = 1,400,000`. O-3 is below the attachment and
recovers 0.

## Hard boundary (never do)

Interpreting *what* a clause says and illustrating *what* the layer arithmetic produces for a
supplied loss is in scope. Deciding that a real claim **is recoverable**, that the reinsurer
**will pay**, what to **bill, collect, reserve, book, or commute**, or whether contested wording
favors the cedent is **out of scope** — that is a recoverability determination or advice.
Surface the facts with citations, label recoveries illustrative, and route judgment questions
per [handoffs.md](handoffs.md).
