# Draft deterministic program comparison: RP-26

Prepared for Cedar Mutual's ceded reinsurance analyst, as of September 18, 2026, US property catastrophe, USD and 2026 treaty period. The supplied stress favors Program B on retained loss plus supplied premiums; the no-loss scenario has lower cost under A. These two deterministic scenarios do not establish which program to buy.

| Scenario | Program | Gross loss | Illustrative recovery | Retained loss | Supplied premium | Retained plus premium |
|---|---:|---:|---:|---:|---:|---:|
| STRESS | A | $15,000,000 | $5,500,000 | $9,500,000 | $1,200,000 | $10,700,000 |
| STRESS | B | $15,000,000 | $8,250,000 | $6,750,000 | $1,950,000 | $8,700,000 |
| ZERO | A | $0 | $0 | $0 | $1,000,000 | $1,000,000 |
| ZERO | B | $0 | $0 | $0 | $1,600,000 | $1,600,000 |

Sources: [reviewed profile](raw-source.md#profile), [A](raw-source.md#program-a), [B](raw-source.md#program-b), [stress events](raw-source.md#stress), [zero-loss alternative](raw-source.md#zero). Exact native values are in `actual-output.json:results.comparisons`; independent arithmetic checks every layer and these totals.

Under A, event 1 recovers $1,000,000 from Q then $1,500,000 from X, retaining $2,500,000. Event 2 recovers $1,500,000 from each layer because both reach remaining aggregate capacity; it retains $7,000,000. Both A layers are exhausted after the two events.

Under B, event 1 recovers $1,250,000 from Q then $750,000 from X, retaining $3,000,000. Event 2 recovers $2,000,000 from Q then $4,250,000 from X, retaining $3,750,000. X is exhausted and Q has $250,000 aggregate capacity left. The second event is applied to capacity remaining after event 1; each alternative scenario resets to the supplied prior erosion.

B's retained-plus-premium figure is $2,000,000 lower under the supplied stress; its no-loss premium is $600,000 higher. No frequency, probability, PML, treaty legal recoverability, variable-premium formula or optimization was inferred. The explicit shared eligibility and sequential remaining-loss convention control this comparison. Ask the program owner to assess contract applicability, broader scenario evidence and purchase objectives before selection or placement.

The artifact is **ready-for-review** with no native findings, and all native and independent checks passed. This is an evidence-workflow status, not professional acceptance or a program recommendation; `recommended_program` is null. No placement or business action occurred. Reviewer disposition remains open. Evidence: [native input](input.json), [validated output](actual-output.json), [independent checks](independent-arithmetic.json).
