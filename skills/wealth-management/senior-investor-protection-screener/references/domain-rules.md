# Signal rules and applicability

These are versioned library screening conventions, not legal tests or empirically calibrated
exploitation predictions. Deployment requires domain/control/fairness acceptance of the
configuration and review routing. Firm policy cannot override applicable law.

[FINRA Rule 2165](https://www.finra.org/rules-guidance/rulebooks/finra-rules/2165) identifies
specified adults as people 65+ or adults 18+ meeting its impairment criterion. This package
uses a trained-human impairment flag for context; it does not establish that legal criterion
or that the firm's activity falls under the rule. [FINRA Rule 4512](https://www.finra.org/rules-guidance/rulebooks/finra-rules/4512)
addresses trusted-contact information. A customer's declined contact is not an exploitation
finding or proof of a rule violation. Both sources reviewed 2026-09-16; a compliance owner
must validate current jurisdiction/capacity applicability before use. Other state/professional
regimes require separately reviewed policies.

## Window and signals
`as_of` includes that entire UTC calendar day. Date-only transaction records represent midnight
UTC; adapters must preserve real time zones where available. The history window begins
`as_of - (lookback_days - 1)`. Baseline rows are within that window and strictly precede the
earliest focal transaction; focal rows are excluded. Only lifecycle=executed records enter
historical baselines or executed outflow aggregates. Proposed/pending focal requests remain
eligible for amount-versus-history, new-payee and account-change screening; their lifecycle
is explicit in every focal evidence row and result.focal_activity. Cancelled activity never
enters executed totals and is not an active focal request. Future focal activity is rejected.
Out-of-window history is excluded, and claimed coverage is checked against requested dates.

| Signal | Rule | Missing evidence |
| --- | --- | --- |
| unusual_disbursement | Focal debit exceeds pre-focal mean plus configured k population standard deviations | Unknown below minimum history or missing configuration/source coverage |
| new_external_payee | High-value focal debit payee absent from the bounded baseline | Unknown if payee or coverage missing; never claims lifetime novelty |
| rapid_liquidation | Sourced executed debit total in configured recent window exceeds threshold | Unknown if window insufficient; name denotes outflow proxy, not confirmed liquidation |
| account_or_beneficiary_change | Sourced recent beneficiary/registration/address change and focal debit | Unknown if changes/config unavailable |
| trusted_contact_gap | Known absent contact or confirmation older than configured recency | Unknown if collection/confirmation unknown; administrative only |
| third_party_influence | Any supplied true third-party/caregiver observation | Unknown if group incompletely assessed and none true |
| capacity_concern_indicators | Any supplied true confusion/recall/repetition observation | Observations only, never a diagnosis |
| communication_red_flags | Any supplied true urgency/secrecy/isolation/scam observation | Unknown if group incompletely assessed and none true |

`fired` is true, false or null. Null means not evaluable. Positive observations are preserved
alongside missing flags, and missing flags remain findings. Never infer negative observations
from an absent block. Age is never itself a concern signal. Under-18 cases retain human
safeguarding routing and do not acquire specified-adult context from an impairment flag.

## Review priority
Exclude `trusted_contact_gap` from exploitation concern counting. Escalate when three concerns
fire or any of rapid liquidation, third-party influence or communications concern fires.
Otherwise Review for any concern; Insufficient evidence with no concern but incomplete data;
Monitor only when there are no concern signals and no data findings. Monitor is not clearance.
These conservatively broad rules require false-positive/false-negative calibration before use.
Any data finding leaves the overall artifact `needs-data`, even with an Escalate priority.

## Configuration and bounds
No fallback thresholds. Require sourced version/owner/capacity/jurisdiction and numeric values
for amount_k (0–10), min_baseline_n (2–10,000), new_payee_amount/liquidation_amount (0–1e12),
cluster_days (1–365), change_window_days/tc_stale_days (1–3650). Day counts and sample counts
must be integers. Lookback is 1–3650 days; at most 10,000 transactions and 1000 changes.
These are computational bounds, not approved regulatory thresholds. Missing parameters create
needs-data; malformed/out-of-bound parameters stop calculation.
