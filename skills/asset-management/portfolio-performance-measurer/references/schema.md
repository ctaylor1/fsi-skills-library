# Native contract

Required common fields: request_id,object_id nonempty strings; as_of and knowledge_cutoff real YYYY-MM-DD; currency three uppercase letters (provider nonmonetary mode may use not-applicable); audience=internal-review; sources[] nonempty (maximum100000) with unique source_ref,version,as_of,known_at. Optional source permitted_audiences,valid_from,valid_to,expires_at are enforced when referenced. Optional unresolved_issues[] contains nonempty strings and is retained.

Every field named source_ref or ending _source_ref must reference the registry. Missing/unregistered, audience-withheld, future-known, future-economic, expired or not-yet-effective evidence fails before calculation. These historical observation methods require source.as_of<=source.known_at<=knowledge_cutoff and source.as_of<=request.as_of. No source truth, license or approval authentication occurs.

Use decimal strings to preserve supplied digits; integers and finite JSON numbers are accepted by the shared Decimal reader. Booleans/null/nonfinite values are not numbers. Supported Decimal inputs have at most38 coefficient digits and exponent/adjusted exponent within+/-38; arithmetic outside the256-digit exact context fails. Domain ratios use explicit precision described below. Except where noted, domain row lists contain1..1000 entries and identifiers are unique. Extra input fields are included in the complete source hash but are not interpreted as instructions or domain facts.

Native output is the foundation envelope: contract_version,skill,request_id,object_id,as_of,knowledge_cutoff,currency,audience,status,draft=true,action_taken=false,human_review_required=true,delivery_status=not-delivered,method,results,unresolved_issues,limitations,handoffs,source_assurance=supplied-unverified,source_refs,input_hash,source_truth=unverified. No original input is embedded. Output validator requires detached original and rejects every altered/extra output field.

## Domain fields

Every mode: return_basis = gross-of-management-fees or net-of-management-fees, period_start, period_end.

`twr`: external_flow_coverage=complete_at_boundaries; subperiods[]{start,end,begin_value_after_flow,end_value_before_flow,net_flow_after,source_ref}. Begin values positive; endings nonnegative; no internal flows.

`modified_dietz`: flow_timing=end-of-day; begin_value,end_value,valuation_source_ref; cash_flows[]{flow_id,date,amount,source_ref}. Positive amount is a contribution to the portfolio. Flow date must be after period_start and no later than period_end. Zero to1000 flows.

`money_weighted`: cashflow_perspective=investor; terminal_value_included=true; cash_flows[]{flow_id,date,amount,source_ref}, 2..1000 rows. Negative means investor investment; positive means investor receipt, including terminal market value. Dates span declared period.

## Numerical precision

Ratios and linked growth factors round to24 decimal places. XIRR uses80-digit numerical arithmetic, at most512 bisections, rate interval tolerance1e-24, relative NPV tolerance1e-24 scaled by max(total absolute flows,1), and maximum36525-day horizon.

Actual period endpoints, received/recorded events and dated valuation observations must also be on or before the request as-of, knowledge cutoff and their own source known-at date. Earlier source metadata cannot validate a later completed observation. Contractual due/payable dates, validity expiries and prospective terms may remain future dated. These chronology checks validate supplied declarations only.
