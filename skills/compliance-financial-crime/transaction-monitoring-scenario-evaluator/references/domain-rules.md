# Domain rules and current authority

Structuring finds the largest qualifying rolling window, including a dense cluster when an older outlier exists. Numeric limit comparisons are inclusive. The legacy pass_through scenario measures aggregate inflow/outflow ratio only; it does not prove rapid movement, provenance of funds, balance depletion, or linkage between particular legs. No scenario deployment or statistical/model validation is implemented. Thresholds and country sets are illustrative configuration requiring owner review.

## Sources checked 2026-09-21

[Wolfsberg 2025 Monitoring for Suspicious Activity Part II](https://wolfsberg-group.org/resources/innovation/202) is nonbinding industry guidance addressing risk coverage, customer/behavioral context and useful monitoring outcomes. It does not certify these scenarios. [FinCEN FAQs, October 9, 2025](https://www.fincen.gov/system/files/2025-10/SAR-FAQs-October-2025.pdf) clarify near-threshold and continuing-review obligations; scenario breaches alone do not determine reportability.

Guidance is distinguished from binding underlying law; illustrative implementation choices are not legal safe harbors. Phase 1 does not certify professional adequacy.


### Evidence-bound replay identity

Velocity uses the same inclusive maximum-limit classification as the ratio scenarios: observed >= baseline × multiplier is BREACH; an observed value at the configured warning boundary is WARN only when below the breach limit.

Fingerprint version `scenario-evidence-v2` binds the complete supplied subject record (including every transaction ID, date, source reference, currency, profile, freshness and observation/baseline period), the actual evaluated rule content, all other supplied assessment context (including as_of, config_version and freshness policy), and the emitted evidence. It uses a full canonical SHA-256 digest. Changing a ledger while preserving aggregate totals is new evidence and cannot be suppressed by the prior fingerprint.

Only invocation `run_id`, prior `open_cases`, and unrelated subjects/rules are excluded from an indicator's evidence identity. This permits the exact same evidence and policy to deduplicate on a later invocation without circularly hashing the dedup baseline. The separate native input_hash still binds the complete original input. Fingerprints are versioned; old aggregate-only fingerprints cannot suppress v2 evidence. There is no persisted case state, source authentication or live alert suppression.
