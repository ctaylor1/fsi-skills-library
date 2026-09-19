# Method and decision boundaries

Authorization rate = approved attempts / all recorded attempts; unknown attempts remain in the denominator and produce an upper bound. Completion = unique completed orders / all extracted orders; upper bound adds pending/unknown orders. Retry-order rate = orders with >1 linked attempt / orders. One order contributes at most once to conversion.

Mature chargeback rate = mature completed orders with chargeback / completed orders with eligible mature known outcomes. Eligibility requires maturity_due <= as_of; none requires chargeback_observed_on >= maturity_due. Zero eligible outcomes yields null. Show excluded completed orders; do not compare a recent immature cohort as though fully observed.

Group by period × currency × channel × method × segment. Differences use current minus baseline within identical dimensions, with no pooled cross-currency money, no automatic population weighting and no statistical attribution. Historical processor declines may be correlated with customer mix, authentication, tokens, incidents or control changes. Hypotheses need source-supported tests, not labels presented as causes.

Each cost row contributes once, with globally disjoint coverage keys. Completed gross value and chargeback face value are informational, never summed with fees into avoided loss or profitability. Review actual fee reconciliation with merchant-payment-cost-analyzer and scenarios with payment-economics-modeler.
