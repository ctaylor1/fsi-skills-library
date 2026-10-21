# Native input schema

The common `compliance-foundation/2.0` envelope is specified in the bundled foundation contract.
The `data` object contains exactly the following native records.

promotion: content_id, content_version, content, sector, product, channel, audience, jurisdiction, perimeter, profile_id, profile_supported; claims[]: claim_id, text, substantiation, risk_balance; disclosures[]: disclosure_id, required, present, visible, conditions_met; approval: actor, actor_authorized, content_id, content_version, audience, product, use_from, use_to. All fields except IDs are facts; profile_supported is an institutional claim, not authenticated legal acceptance.

A fact holds `value`, `source_refs` and `fact_ids` under the common contract; use null with explicit unknown/conflict source status when unavailable. Match exact value and type to the mapped source fact, including empty/zero/false facts. Identity values are not interchangeable across cases. Unknown fields and malformed dates/counts stop intake. Substantive missingness proceeds only as an unresolved draft.

Native object_type: `financial_promotion`. The executable `domain.py` schema is authoritative for the exact required fields/types; all data record IDs are internal labels, and consequential identity/context values are claims.

## Complete field inventory

Each listed consequential field is an exact claim object `{value, source_refs, fact_ids}`.
Only the row label named below is a plain internal ID. Empty evidence-reference lists preserve
unknowns; malformed types/fields stop intake.

- `data.promotion`: `content_id`, `content_version`, `content`, `sector`, `product`, `channel`, `audience`, `jurisdiction`, `perimeter`, `profile_id`, `profile_supported`, `profile_authority`, `profile_basis`, `use_from`, `use_to`.
- `data.approval`: `actor`, `actor_authorized`, `content_id`, `content_version`, `audience`, `product`, `sector`, `jurisdiction`, `channel`, `profile_id`, `authority_scope`, `approved_on`, `use_from`, `use_to`.
- `data.claims[]`: row label `claim_id`; claims `text`, `substantiation`, `substantiation_state`, `risk_balance`.
- `data.disclosures[]`: row label `disclosure_id`; claims `text`, `required`, `present`, `visible`, `conditions_met`.
