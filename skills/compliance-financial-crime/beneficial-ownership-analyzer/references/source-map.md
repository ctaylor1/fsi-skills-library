# Supplied input and output contract

Required: `case_id`, `as_of`, `jurisdiction`, `config_version`, `legal_entity.entity_id`, graph nodes/edges, applicable policy profile and full `config`. Every entity node must explicitly declare `structure_type: corporation`; other/missing legal structures are unsupported. Ownership/control/document rows carry supplied `source_ref`; graph targets are validated; duplicate edges are rejected rather than double-counted.

Configuration requires `ownership_threshold_pct`, `require_control_prong`, `min_control_persons`, `document_required_for_ubo`, `doc_max_age_days`, `pct_tolerance`, `aggregate_across_chains`, `ownership_test`, `qualifying_control_types`, `document_types`. No legal authority/effective date is silently supplied. Declared owners have person_id and ownership/control basis. Documents have doc_id, type, subject, issued, expires, source_ref.

Output preserves `computed_owners`, `control_persons`, `ubos` (candidate label for compatibility), declarations, gaps and readiness; adds excluded controls, limitations and detached source binding.

## Policy and source provenance

Every run requires the explicit policy_profile and execution_context described in [SKILL.md](../SKILL.md). Profile owner authority is supplied, not authenticated. Test fixtures identify a synthetic test bank, synthetic authority and no actual approval. Do not deploy their weights, lists, thresholds or requirements as law.

Original source records remain separate from the native output. Source references/excerpts are assertions from the input; no live retrieval, record-system precedence, authenticity, completeness or access entitlement is implemented. Preserve conflicts, stale evidence and retrieval limits for human review. Input-field observations are not external-source evidence.

Use [the shared evidence contract](evidence-contract.md) and [source governance](source-governance.md) for the distinct workflow envelope, provenance and applicability requirements. Native hash/reconstruction checks establish reproducibility only.
