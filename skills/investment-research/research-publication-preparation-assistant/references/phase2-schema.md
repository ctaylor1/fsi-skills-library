# Native schema

All Phase 2 inputs carry schema_version=ir-phase2/1.0, request_id,purpose=internal-research,audience=internal-review,subject{type,id,issuer_id for security},as_of,use_on,aware knowledge_cutoff,information_barrier,sources[],top-level evidence_refs[],unresolved_issues[]. Every row citation must be nonempty, registered and also declared at top level for source permission/time gating. Supplied future or ineligible evidence withholds the result projection. The example is synthetic; no entitlement or authenticity is asserted.

`note` requires note_id,intended_audience,jurisdiction,research_type,institution. `policy_profile` requires profile_id,version,institution,jurisdiction,audience,research_type,effective_from,effective_to,applicability_status=confirmed-supplied/unknown,evidence_refs. Disclosures[] have disclosure_id,required boolean,status=present-supplied/absent/unknown; present disclosures need note_anchor,supplied_text,evidence_refs. Restricted_list_review status checked-supplied/unknown; checked rows need snapshot_date,evidence_refs; subject_restricted is boolean or null. Source_permissions[] has source_id,status=allowed-supplied/denied/unknown,valid_from,valid_to,audiences[],purposes[],evidence_refs.

See the paired JSON fixtures under evals/files; the separately retained original is mandatory for output reconstruction.
