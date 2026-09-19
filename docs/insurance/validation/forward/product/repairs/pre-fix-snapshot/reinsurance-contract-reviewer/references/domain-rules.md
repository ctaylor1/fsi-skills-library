# Treaty explanation and supported illustration

Explain the supplied clauses with source text and citations preserved. Contract interpretation,
claim eligibility, legal effect, actuarial selection and booked recoverables remain distinct.

## Numeric support boundary

Only `treaty_type: excess_of_loss`, one layer, `illustration_basis: losses_occurring`,
and a nonempty `illustration_basis_source` support numeric illustration. All losses require
`eligible_for_illustration` (boolean) and `eligibility_source_ref` from a reviewer. Dates must
be ascending and within the supplied inclusive treaty period. These are supplied assumptions,
not facts inferred or approved by the agent. Missing assumptions suppress the entire aggregate
illustration because an earlier unknown event can affect later available capacity.

Other treaty types may receive sourced explanations, but no XoL arithmetic. Time-based,
exhaustion-triggered and other reinstatement terms require a separately validated method.

## Layer and aggregate calculation

For each supplied eligible occurrence:

```
layer_loss = min(max(gross_loss - attachment, 0), limit)
ceded = min(layer_loss, max(aggregate_limit - cumulative_before, 0))
cumulative_after = cumulative_before + ceded
remaining_aggregate = aggregate_limit - cumulative_after
```

A reviewer-supplied ineligible event contributes zero; the agent never determines eligibility.
The aggregate limit must be explicit. A 10m limit excess of 5m produces 7m on an eligible 12m
loss before aggregate effects.

## Supported reinstatement premium

`reinstatement_basis: pro_rata_amount_on_erosion` requires an explicit reinstatement count,
one `premium_pct` per reinstatement and `layer_premium`. For k from 0 to count−1, calculate
the overlap of `(cumulative_before, cumulative_after]` with `[k*limit,(k+1)*limit]`.
The restored amount is the sum of these overlaps; premium is the sum of
`overlap/limit * premium_pct/100 * layer_premium`. Restoration is capped at count*limit.
There is no time adjustment. Never apply this method to wording providing a different trigger.

The synthetic 10m xs 5m example has one reinstatement at 100%, a 2m layer premium and 20m
aggregate. Losses 12m, 18m and 3m produce ceded 7m, 10m and 0; restored amounts 7m, 3m and 0;
additional premiums 1.4m, 0.6m and 0. Totals are 17m ceded and 2m reinstatement premium.

## Validation

Retain exact input assumptions and clause text. Validate structural inputs before calculation,
then recompute the complete illustration—including reinstatement premiums—from the preserved
input when checking output. A content hash is not source authenticity or a recoverability opinion.
