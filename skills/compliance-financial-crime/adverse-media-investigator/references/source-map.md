# Supplied input and output contract

Required: config_version, as_of_date, subjects, policy_profile and full scoring_config. Config contains category_weight, assertion_addend, source_tier_addend (string keys 1/2/3), recency, material_min, watch_min, coverage_max_age_days. There are no fallback approved scores.

Each subject has unique subject_id, name, person/entity type, optional DOB/known_identifiers, hits and search_coverage. Hits carry hit_id, source, source_ref, headline, excerpt, category, assertion_type, source_tier, publication/event dates, match_evidence and optional matter_id/supersedes_hit_ids. Match evidence fields: field (name/dob/identifier), subject_value, source_value, source_ref, source_excerpt. Date gaps remain unknown rather than being substituted.

Output cases retain matched, discarded and unresolved hits; separate event/publication chronology; nullable materiality score; scoped recommendation; routes; needs; search coverage and source limitations. Native output is reconstructed against the detached batch.

## Policy and source provenance

Every run requires the explicit policy_profile and execution_context described in [SKILL.md](../SKILL.md). Profile owner authority is supplied, not authenticated. Test fixtures identify a synthetic test bank, synthetic authority and no actual approval. Do not deploy their weights, lists, thresholds or requirements as law.

Original source records remain separate from the native output. Source references/excerpts are assertions from the input; no live retrieval, record-system precedence, authenticity, completeness or access entitlement is implemented. Preserve conflicts, stale evidence and retrieval limits for human review. Input-field observations are not external-source evidence.

Use [the shared evidence contract](evidence-contract.md) and [source governance](source-governance.md) for the distinct workflow envelope, provenance and applicability requirements. Native hash/reconstruction checks establish reproducibility only.
