# Domain Rules — policy-renewal-reviewer

Explainable renewal **material-change findings** and how they map to a **review-disposition band**.
Thresholds are configuration (versioned, owned by the underwriting/actuarial function), not hard-coded
judgments, and never tuned to an individual insured. The firm's underwriting standard and any filed
rate/rule takes precedence over these defaults.

## Finding taxonomy

| Finding | Fires when (default config) | Evidence attached |
| ------- | --------------------------- | ----------------- |
| `premium_change` | `abs(premium delta %) >= premium_change_pct` (default 10%) | Expiring + proposed annual premium |
| `exposure_change` | Any shared exposure basis moves `>= exposure_change_pct` (default 10%) | Changed basis: expiring/proposed/delta% |
| `limit_reduced` | Any coverage present on both terms has a **lower** proposed limit | Coverage + expiring/proposed limit |
| `deductible_increased` | A coverage deductible rises `>= deductible_increase_pct` (default 20%; any increase from 0) | Coverage + expiring/proposed deductible |
| `coverage_removed` **(escalator)** | A coverage on the expiring term is **absent** from the proposed term | Removed coverage + expiring limit |
| `coverage_added` | A coverage on the proposed term is **not** on the expiring term | Added coverage + proposed limit |
| `form_endorsement_change` | A `form_id` is added, removed, or its `edition` changed | The changed/added/removed forms |
| `loss_ratio_flag` **(escalator)** | `incurred / (expiring premium x years) >= loss_ratio_threshold` (default 0.70) | Claim rows + computed basis |
| `large_open_claim` | A claim's `incurred >= large_claim_incurred` (default 100,000) **or** `status == open` | The large/open claim rows |
| `rate_exposure_divergence` | `abs(premium % - primary-exposure %) >= rate_exposure_tolerance_pct` (default 5pt) | Premium % + primary-exposure % + divergence |

Findings are **additive and independent**; the output reports each that fired with its own evidence.
There is no opaque composite "renewal score". When required data is absent (e.g. no claims, no
exposures, no forms) the finding is reported as `not_evaluable`, not as "no change".

## Disposition mapping (deterministic, documented)

| Suggested band | Rule |
| -------------- | ---- |
| **Routine** | 0 findings fired |
| **Review** | 1–2 findings fired, none of them an escalator |
| **Escalated** | ≥ 3 findings fired, OR any escalator (`coverage_removed`, `loss_ratio_flag`) fired |

The disposition is a **triage suggestion for a human reviewer/underwriter**. It is not a renewal,
pricing, or coverage determination and it never triggers a policy action. The same mapping is
enforced in `scripts/calculate_or_transform.py` and re-checked in `scripts/validate_output.py`.

## Renewal questions (drafted per fired finding)

Each fired finding yields one **non-directive question** for the human to raise with the insured or the
underwriter (e.g. "Confirm whether the coverage limit reduction is intended and remains adequate").
Questions surface what to ask; they never state a decision, a price, or advice.

## Hard boundaries (fail closed)

- Never state or imply that the policy **will** renew, non-renew, or be declined, and never set,
  quote, or commit a **premium/rate/deductible**.
- Never **bind** coverage or **issue a non-renewal / cancellation notice**.
- Never make a **coverage or claim determination**, and never give **personalized insurance advice**.
- Never tune thresholds to the individual insured, and never attribute intent or cause to a premium
  change — report the factual delta and the rate-vs-exposure divergence for the underwriter to explain.

## Context prompts (always include when a finding fired)

Exposure growth, inflation guard, a scheduled rate filing, bureau/state mandatory form changes,
insured-requested limit/deductible changes, updated valuations, loss development / large-loss
treatment / credibility on the loss ratio, and data corrections in exposure basis. The pack must invite
the reviewer to weigh these benign explanations before drawing any conclusion.
