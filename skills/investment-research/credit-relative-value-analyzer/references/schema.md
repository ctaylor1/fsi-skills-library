# Native schema

All Phase 2 inputs carry schema_version=ir-phase2/1.0, request_id,purpose=internal-research,audience=internal-review,subject{type,id,issuer_id for security},as_of,use_on,aware knowledge_cutoff,information_barrier,sources[],top-level evidence_refs[],unresolved_issues[]. Every row citation must be nonempty, registered and also declared at top level for source permission/time gating. Supplied future or ineligible evidence withholds the result projection. The example is synthetic; no entitlement or authenticity is asserted.

`target` and nonempty `peers[]` have unique security_id,issuer_id,currency,option_profile,rating_group,spread_basis,unit=bps,nullable spread_bps,nullable nonnegative duration,price_date,aware known_at,evidence_refs. `duration_tolerance` is nonnegative. `max_price_age_days` is a nonnegative integer. knowledge_cutoff is an aware timestamp for price-vintage comparisons.

See the paired JSON fixtures under evals/files; the separately retained original is mandatory for output reconstruction.
