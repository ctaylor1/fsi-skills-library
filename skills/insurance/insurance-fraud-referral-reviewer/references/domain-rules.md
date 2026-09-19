# Domain rules — Insurance Fraud Referral Review

- Default catalogue weights: late report 2; early loss 3; post-increase loss 3; claim frequency 2; absent report 2; documentation gap 1; inconsistent statements 2; lapse/reinstatement 2; sourced open prior-SIU context 3.
- Defaults: late report >30 days; early loss <=60 days; post-increase <=30 days; prior count >=3; inconsistencies >=2. Thresholds and weights must be finite nonnegative; refer_min must exceed positive monitor_min. Defaults refer>=6, monitor>=3.
- Only an explicitly reportable loss with police_report:false triggers absence. Unknown police report, inception, counts or flags stay in unknown_inputs and make assessment partial.
- Prior SIU history requires an explicit open status and source for its indicator. It never overrides the numerical referral threshold; closed/unknown history is not an adverse finding.
- Known indicators can still recommend human referral/monitoring with unresolved context; an insufficient known score plus unknown inputs produces needs-data. A low complete score is insufficient-indicators, not clearance or case closure.
- Counterevidence is retained in the structured record and draft. It is not automatically subtracted from unrelated indicators; the SIU reviewer evaluates its relevance.
- Output validation reconciles indicator IDs/weights/sum, band/recommendation and pending approvals. Source counterevidence is preserved verbatim; assistant-authored accusations remain prohibited.

## Scope limit
Nine configured claim indicators only. No fraud truth determination, causal inference, model probability, investigator case management, regulatory referral filing or cross-party identity matching.
