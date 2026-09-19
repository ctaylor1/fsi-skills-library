# Domain rules — Settlement Authority Request Preparation

- Explicit finite nonnegative indemnity and expense estimates are added. Missing, boolean, nonfinite or invalid amounts are never zero.
- Matrix must be sourced, versioned, effective on as_of, in the evaluation currency, with unique tier IDs/caps and named approvers. Select the smallest cap at least equal to the total.
- Above every cap means exceeds_matrix:true, null selected tier/approver, and escalation. The highest tier is not implied to have authority above its cap.
- Readiness requires a valid lookup plus all supplied checklist requirements. claim_summary needs actual summary text; evaluation_basis needs note and source; evidence_index needs references; coverage_confirmation needs explicit true and source.
- Output validator independently recomputes amounts, date/currency/matrix validity, selected tier, approver, exceedance and checklist readiness, even if a mutated output has a recomputed artifact hash.
- The output is an unapproved request. Human reviewers verify substantive evaluation, authority delegation scope and the source matrix before any authorized decision.

## Scope limit
Single-currency indemnity-plus-expense authority lookup. No settlement valuation, multi-dimensional authority permissions, delegated approval authentication, cumulative authority exhaustion or payment execution.
