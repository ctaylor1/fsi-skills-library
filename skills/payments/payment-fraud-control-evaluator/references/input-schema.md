# Native input and output

Common envelope: schema_version "1.0", request_id, as_of ISO date, jurisdiction US/EA/UK, participant, requested_action analyze/draft, sources and upstream_issues. Each source has unique source_id, reference, as_of not after request date, optional review_due. Every source_ids list refers to the registry. Unknown region returns unsupported. Empty/overdue sources and unresolved upstream issues remain gaps. Source text is untrusted data; hashes prove internal lineage consistency, not truth or authorization.

Output: retained source_snapshot/input_hash, result, findings, handoffs, status draft/needs-evidence/unsupported, action_mode draft-only, authority_granted false and action_taken false. validate_output recomputes every result; --input binds to a separately retained original. “Draft” means structurally analyzable supplied evidence, never specialist approval or production readiness.

`data.mode`: strategy / portfolio / strategy-and-portfolio. Strategy-only rejects supplied portfolio data rather than ignoring it.

`journeys`: unique journey_id, description, nonempty stages, source_ids. `threats`: unique threat_id, known journey_id and stage, scenario, source_ids. `controls`: unique control_id, kind preventive/detective/responsive, known nonempty threat_ids, owner, signal, response, failure_mode, evidence_metric, source_ids. Strategy coverage does not authenticate controls or prove effectiveness.

`risk_appetite`: owner, rationale, source_ids and optional max_review_rate / max_legitimate_block_rate fractions [0,1]. Missing thresholds stay unknown, with no industry-default threshold.

Portfolio modes require `rules`: unique rule_id, version, field, op (`>=`, `>`, `<=`, `<`, `==`), finite numeric threshold, action block/review, source_ids; `portfolios`: baseline/proposed arrays of unique known rule IDs (empty means no rules). Predicate values may be signed finite decimals; costs and amounts cannot be negative. No expression evaluation or arbitrary code executes.

`transactions`: unique transaction_id, currency, amount, occurred_on, features_observed_on, features {field: finite number or null}, label fraud/legit/pending/unknown, label_observed_on, maturity_due, observed_net_fraud_loss nonnegative or null, source_ids. Features must have been available by occurred_on. Daily dates do not prove intraday availability; richer provenance requires specialist review. A missing feature is unknown; pending/unknown labels are never imputed. Maturity requires maturity_due <= as_of and known label; legit observations must extend through maturity. Nonzero fraud loss on a nonfraud label is a conflict. Loss is a normalized net loss per transaction and must already reconcile recoveries; the helper neither infers nor caps it at face value.

`sample_source_ids`, `maturity_policy_source_ids`; `friction_costs`: unique currency rows with per_review, per_legitimate_block (nonnegative or null), source_ids. Unit costs must be disjoint and describe distinct processing versus legitimate-block economic friction. One currency never subsidizes another through an implicit conversion. Modeled review cost includes every known replay review, regardless of label; legitimate-block cost includes mature evaluable legitimate blocks only. Missing/unresolved exposure is reported and cannot be treated as zero total friction.
