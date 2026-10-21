# Domain method and schema

The native method validates inventory and relationship IDs, then builds a many-to-many provision/component adjacency matrix. Required dimensions are policies, processes, controls, systems, data, evidence and owners unless a source-backed scoped exception is supplied. A relationship supports coverage only when both component existence and relationship facts are supported and applicable; non-applicable provisions are shown outside the coverage denominator. All components with no mapped provision are retained as orphans. No operating effectiveness result is inferred.

## Common evidence contract

Read `scripts/foundation_contract.py` for the exact common contract and [evidence contract](evidence-contract.md) for professional provenance. Every consequential input uses a claim `{value, source_refs, fact_ids}` with exact registry facts; records cannot cite an unrelated source field to establish their own status. Common validation retains stale/conflicting/missing evidence and requires detached original input. Unsupported legal profiles and methods remain open.

## Native payload

`provisions`: nonempty `{id, text_fact, applicability_fact, scope, required_dimensions}`. `components`: `{id, dimension, existence_fact, scope}` where dimension is `policies|processes|controls|systems|data|evidence|owners`. `links`: `{provision_id, component_id, relation_fact}`. `exceptions`: `{provision_id, dimension, justification_fact}`. References must be valid and relationships unique.

The fixture in `evals/files/input.json` is de-identified synthetic supplied policy and illustrative evidence. It does not assert a real institution, live rule, independently tested control or actual legal acceptance. The native result retains detached claim-path/source/fact locators and consistency states; these locators do not establish semantic truth or automatic conclusion support. Domain findings preserve their open issues.

## Practitioner questions

Which entity, activity, population and date does each finding concern? Who owns the extracted source text and contested interpretation? What material evidence is missing or conflicting? Which conclusion is a fact, supplied institutional policy, method assumption or recommendation? What adjacent specialist must review before this artifact can be relied upon?

All seven required dimensions must remain in each provision universe; handle a reviewed dimension exception explicitly. Component `existence_fact.value` exactly equals `{component_id, dimension, scope, status: "present"}`; `relation_fact.value` equals `{provision_id, component_id}`. Exception `justification_fact.value` requires `{provision_id, dimension, scope, reviewed_status: "accepted", reason}` matching the exact provision/dimension/scope. Exception acceptance is supplied and still needs institutional review.
