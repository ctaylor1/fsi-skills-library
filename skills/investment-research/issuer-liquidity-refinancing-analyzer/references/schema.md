# Native schema

All Phase 2 inputs carry schema_version=ir-phase2/1.0, request_id,purpose=internal-research,audience=internal-review,subject{type,id,issuer_id for security},as_of,use_on,aware knowledge_cutoff,information_barrier,sources[],top-level evidence_refs[],unresolved_issues[]. Every row citation must be nonempty, registered and also declared at top level for source permission/time gating. Supplied future or ineligible evidence withholds the result projection. The example is synthetic; no entitlement or authenticity is asserted.

`currency`,`unit`,`horizon_end`,`minimum_cash` and boolean `maturity_inventory_complete` are explicit. `cash{unrestricted,restricted,evidence_refs}` permits unknown cash. Lists cash_flows,maturities,facilities,refinancing require unique id,date,currency,unit,evidence_refs. Cash flows carry signed net_operating_flow, nonnegative mandatory_capex,cash_interest. Maturities carry instrument_id and nullable nonnegative amount. Facilities carry nullable undrawn, committed boolean, conditions_status=satisfied-supplied/unsatisfied/unknown, expiry. Refinancing carries nonnegative amount and status=committed-supplied/assumed/unknown. `stress` carries burn_multiplier>=1 and facility_haircut/refinancing_haircut fractions [0,1].

See the paired JSON fixtures under evals/files; the separately retained original is mandatory for output reconstruction.

Facilities additionally carry explicit repayment_date (date or null). Unknown repayment dates exclude capacity. Capacity is a hypothetical full draw at availability, with the same modeled draw repaid on the supplied repayment date when inside the horizon. Existing debt maturities exclude this incremental modeled capacity repayment to avoid double counting.
