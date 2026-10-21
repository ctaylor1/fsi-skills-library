# Supplied input and output contract

Required: `customer_id`, `as_of`, `methodology_version`, applicable profile, explicit `config`, sourced `rating_of_record`. Factors carry name, risk_value, weight, scale_max if supplied, observed_date and source_ref. Missing dates/factors remain incomplete.

`config` requires `factor_catalog` (each spec: max_weight, scale_max, required; optional floor_at_max), `band_thresholds`, `band_order`, `staleness_days`, `override_max_days`, `trigger_types_requiring_review`. Thresholds ascend in band order and end at 100. Overrides and trigger records are retained for human review.

Output includes nullable scores/bands, `assessment_status`, cited factor details/findings, `overrides_review`, recommendation and human-adjudication flag. The rating of record is retained as a supplied record, not changed.

## Policy and source provenance

Every run requires the explicit policy_profile and execution_context described in [SKILL.md](../SKILL.md). Profile owner authority is supplied, not authenticated. Test fixtures identify a synthetic test bank, synthetic authority and no actual approval. Do not deploy their weights, lists, thresholds or requirements as law.

Original source records remain separate from the native output. Source references/excerpts are assertions from the input; no live retrieval, record-system precedence, authenticity, completeness or access entitlement is implemented. Preserve conflicts, stale evidence and retrieval limits for human review. Input-field observations are not external-source evidence.

Use [the shared evidence contract](evidence-contract.md) and [source governance](source-governance.md) for the distinct workflow envelope, provenance and applicability requirements. Native hash/reconstruction checks establish reproducibility only.
