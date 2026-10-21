# Native schema

All Phase 2 inputs carry schema_version=ir-phase2/1.0, request_id,purpose=internal-research,audience=internal-review,subject{type,id,issuer_id for security},as_of,use_on,aware knowledge_cutoff,information_barrier,sources[],top-level evidence_refs[],unresolved_issues[]. Every row citation must be nonempty, registered and also declared at top level for source permission/time gating. Supplied future or ineligible evidence withholds the result projection. The example is synthetic; no entitlement or authenticity is asserted.

`instrument_id` and `documents[]` are required. Document rows carry document_id,unique version,effective_date,executed boolean,supersedes_version null for base or exact predecessor,terms[],changes[],evidence_refs. A term has term_id,field,raw_text,value,interpretation_status=reviewed-explicit/unresolved,evidence_refs. Changes have term_id,action=add/replace/delete,reviewed boolean,evidence_refs; replace/delete requires prior_value_hash of the current term value; add/replace requires new_term. A reviewed-covenant-test-definition term may carry a complete explicit native covenant test in value. No raw clause is translated automatically.

See the paired JSON fixtures under evals/files; the separately retained original is mandatory for output reconstruction.

Required document_inventory_complete is an explicit supplied boolean asserting coverage of the relevant governing base agreement and amendments. False yields partial and cannot be promoted into a reviewed covenant adapter. A missing predecessor withholds the current governing_version and all effective values.
