# Native schema

All Phase 2 inputs carry schema_version=ir-phase2/1.0, request_id,purpose=internal-research,audience=internal-review,subject{type,id,issuer_id for security},as_of,use_on,aware knowledge_cutoff,information_barrier,sources[],top-level evidence_refs[],unresolved_issues[]. Every row citation must be nonempty, registered and also declared at top level for source permission/time gating. Supplied future or ineligible evidence withholds the result projection. The example is synthetic; no entitlement or authenticity is asserted.

`issuer_profile` must be `nonfinancial-corporate`. `financials` carries currency, unit, accounting_basis, consolidation_scope, period{start,end,fiscal_calendar_id}, evidence_refs and nullable EBITDA, gross_debt, unrestricted_cash, interest_expense, operating_cash_flow, capex, funds_from_operations. `instruments[]` requires instrument_id,issuer_id,estate_id,seniority,currency,nullable principal,guarantor_ids,evidence_refs. Optional ebitda_adjustments[] uses adjustment_id,amount,rationale,evidence_refs. Optional risk_observations[] uses risk_id,category,observation,evidence_refs.

`financials` is reported historical information: its period must end on or before
both `as_of` and the UTC calendar date of `knowledge_cutoff` (or the supplied
cutoff date when date precision is declared). Forecast and scenario financials
are unsupported and cannot be relabeled as reported ratios. This period check
does not constrain an instrument's future contractual maturity.
Each `ebitda_adjustments[].adjustment_id` must be unique across the request;
identical or conflicting rows with the same ID are rejected before arithmetic.
IDs identify supplied adjustments; the analyst must still reconcile different
IDs that may describe the same economic item.

See the paired JSON fixtures under evals/files; the separately retained original is mandatory for output reconstruction.
