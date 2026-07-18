# Domain Rules — earnings-results-analyzer

Explainable beat/miss **classification** and how the headline lines map to an **overall
result band**. Tolerances, the headline-metric set, and the mapping are configuration
(versioned, owned by the research/coverage team), not hard-coded judgments. Nothing here
produces a rating, a price target, or a recommendation — the analysis is factual and the
investment view is a human, supervised decision.

## Per-metric surprise and classification

For each reported metric with an estimate:

```
raw_surprise = (actual - estimate) / abs(estimate)
effective    = raw_surprise            if direction == higher_is_better
             = -raw_surprise           if direction == lower_is_better
```

| Classification | Fires when (default config) |
| -------------- | --------------------------- |
| **Beat**    | `effective >= beat_tol` (default 0.02) |
| **Miss**    | `effective <= -miss_tol` (default 0.02) |
| **In-line** | within the tolerance band |
| **not_evaluable** | no estimate (or a zero estimate) to compare against |

`direction` matters: expenses, net debt, churn, and cost ratios are `lower_is_better`, so a
figure **below** the estimate is a **Beat**. Evidence attached: the reported actual **and**
the estimate it is measured against, each cited.

## Guidance classification

Using prior vs. new midpoints (or a `withdrawn` flag):

| Classification | Rule |
| -------------- | ---- |
| **Withdrawn**   | guidance marked withdrawn |
| **Initiated**   | no prior range, a new range issued |
| **Raised**      | new midpoint moves in the favorable direction by more than `guidance_tol` (default 0.5% of prior midpoint) |
| **Lowered**     | new midpoint moves against the favorable direction by more than `guidance_tol` |
| **Maintained**  | new midpoint within `guidance_tol` of prior |
| **not_evaluable** | no new range and not marked withdrawn |

## Transcript observations

Language changes are surfaced **factually and cited**, never scored: a topic with prior and
current language is a "change"; a topic with only current language is a **new disclosure**,
not a change. No sentiment number is assigned.

## Overall result mapping (deterministic, documented)

Driven only by the metrics flagged `headline` (typically revenue and EPS), with a
headline-guidance cut:

| Overall result | Rule |
| -------------- | ---- |
| **Undetermined** | no headline metric is evaluable |
| **Miss**    | ≥ 1 headline metric Miss and 0 headline Beats |
| **Mixed**   | headline Beats and Misses both present; OR headline Beats/In-line but a **headline** guidance item was **Lowered/Withdrawn** |
| **Beat**    | ≥ 1 headline Beat, 0 headline Misses, and no headline guidance cut |
| **In-line** | all headline metrics In-line and no headline guidance cut |

The overall result is a **factual description of the print versus expectations**. It is not a
rating, a price target, or a recommendation, and it never triggers a trade.

## Hard boundaries (fail closed)

- Never issue or imply an **investment rating** (buy/sell/hold, overweight/underweight),
  **price target**, or **recommendation/personalized advice** — describe results factually
  and attribute the view to the human analyst.
- Never **initiate/upgrade/downgrade coverage**, **publish** a note, or **trade** on the read.
- Never **tune tolerances** to manufacture a beat/miss; use only the versioned config.
- Never fold in **MNPI** or breach information barriers to "improve" the analysis.

## Thesis considerations (always include when findings exist)

Quality of the beat/miss (volume vs. price vs. one-offs: restructuring, tax, FX, non-recurring
items); guidance change vs. buy-side/whisper expectations already in the price; durability of
KPI drivers vs. pull-forward or seasonality; mix shift and margin trajectory vs. the prior
trend; capital-allocation changes (buyback/dividend) and balance-sheet effects; the direction
of consensus revisions implied by the print. These prompt the analyst to weigh both sides
before forming any view.
