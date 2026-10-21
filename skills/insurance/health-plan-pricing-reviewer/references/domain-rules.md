# Method and limits

Use the supplied health pricing actuary's cohort renewal basis. Reconcile complete
member months and categories to the same period, valuation date, currency,
population and benefit basis. Never replace exposure with a snapshot count or
silently prorate, annualize, infer IBNR, choose trend or normalize categories.

For each source-complete category:

- Net incurred = paid + case outstanding excluding IBNR + IBNR - separate recovery.
- Adjusted incurred = net incurred + signed base-incurred adjustments.
- Base PMPM = adjusted incurred / base member months.
- Projected PMPM = base PMPM × supplied cumulative cost factor × supplied cumulative
  utilization factor + signed projection-PMPM adjustments.

Sum projected categories. Nonpremium expense PMPM = fixed projection dollars /
projected member months + supplied expense PMPM. Conditional premium PMPM =
(projected claim PMPM + nonpremium expense PMPM) /
(1 - premium-proportional expenses - premium-proportional margin).
Renewal change fraction = conditional premium / comparable current premium - 1.
The descriptive base incurred/earned-premium ratio is not statutory MLR or a rebate
calculation. All sums, products and ratios use exact rational intermediates; terminating
decimal outputs remain exact. Recurring ratios are rendered at 50 significant
digits and explicitly labeled, with no monetary rounding policy. Inputs are bounded
to 256 significant digits and exponent magnitude 1000.

Trend factors are already cumulative over the explicit stated horizon. This
method performs no annual compounding, fitted trend, credibility blending,
underwriting classification, index-rate/metal-tier construction, risk adjustment
model, rate approval or filing. Record recovery, reinsurance and benefit adjustments
once with unique economic event IDs; disclose their stage and basis. Unsupported
negative net costs, zero denominators, scope mismatches or any missing dependency
produce null derived measures. Professional adequacy, fairness and applicability
remain with the pricing actuary and applicable institutional reviewers.
