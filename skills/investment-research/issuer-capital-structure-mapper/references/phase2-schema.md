# Native schema

All Phase 2 inputs carry schema_version=ir-phase2/1.0, request_id,purpose=internal-research,audience=internal-review,subject{type,id,issuer_id for security},as_of,use_on,aware knowledge_cutoff,information_barrier,sources[],top-level evidence_refs[],unresolved_issues[]. Every row citation must be nonempty, registered and also declared at top level for source permission/time gating. Supplied future or ineligible evidence withholds the result projection. The example is synthetic; no entitlement or authenticity is asserted.

`instruments[]` requires instrument_id,issuer_id,estate_id,security_id,priority_basis,currency,unit,document_id,document_version,evidence_refs; principal and coupon_pct nullable nonnegative, maturity_date valid date or null, secured boolean or null,guarantee_inventory_complete boolean,guarantor_ids[],collateral_ids[]. `priority_links[]` has senior_instrument_id,junior_instrument_id,basis,evidence_refs; links must reference supplied instruments and form an acyclic graph.

See the paired JSON fixtures under evals/files; the separately retained original is mandatory for output reconstruction.

`instrument_inventory_complete` is a required supplied boolean covering the single declared legal issuer. False remains partial. Each instrument issuer_id must equal subject.issuer_id (security subject) or subject.id (issuer subject); subsidiary issuers require separate maps. Group principal_complete/maturity_complete concern only supplied rows and do not prove inventory completeness.
