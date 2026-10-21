# Native schema

All Phase 2 inputs carry schema_version=ir-phase2/1.0, request_id,purpose=internal-research,audience=internal-review,subject{type,id,issuer_id for security},as_of,use_on,aware knowledge_cutoff,information_barrier,sources[],top-level evidence_refs[],unresolved_issues[]. Every row citation must be nonempty, registered and also declared at top level for source permission/time gating. Supplied future or ineligible evidence withholds the result projection. The example is synthetic; no entitlement or authenticity is asserted.

`estates[]` uses estate_id,currency,unit,nonnegative unencumbered_value,estate_costs,evidence_refs and collateral_pools[{globally unique pool_id,nonnegative value,release_surplus_to_estate boolean,evidence_refs}]. `claims[]` uses claim_id,estate_id,currency,unit,nonnegative amount,positive integer priority,evidence_refs. Secured claims also require pool_id in the same estate,collateral_cap<=claim amount,positive collateral_priority,deficiency_allowed boolean or null.

See the paired JSON fixtures under evals/files; the separately retained original is mandatory for output reconstruction.
