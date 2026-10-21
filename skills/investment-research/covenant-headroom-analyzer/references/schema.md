# Native schema

All Phase 2 inputs carry schema_version=ir-phase2/1.0, request_id,purpose=internal-research,audience=internal-review,subject{type,id,issuer_id for security},as_of,use_on,aware knowledge_cutoff,information_barrier,sources[],top-level evidence_refs[],unresolved_issues[]. Every row citation must be nonempty, registered and also declared at top level for source permission/time gating. Supplied future or ineligible evidence withholds the result projection. The example is synthetic; no entitlement or authenticity is asserted.

`tests[]` is nonempty, unique test_id. Each test requires instrument_id,document_id,document_version,definition_id,accounting_basis,currency,unit,test_date,effective_from/optional effective_to,period{start,end},application_status,definition_reviewed boolean,operator=maximum/minimum,nonnegative threshold,evidence_refs. Numerator and denominator each carry definition, matching period and nonempty components[{component_id,nullable amount,sign=-1/1,evidence_refs}].

See the paired JSON fixtures under evals/files; the separately retained original is mandatory for output reconstruction.
