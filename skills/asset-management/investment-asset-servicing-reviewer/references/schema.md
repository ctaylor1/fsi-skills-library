# Native contract

Required common fields: request_id,object_id nonempty strings; as_of and knowledge_cutoff real YYYY-MM-DD; currency three uppercase letters (provider nonmonetary mode may use not-applicable); audience=internal-review; sources[] nonempty (maximum100000) with unique source_ref,version,as_of,known_at. Optional source permitted_audiences,valid_from,valid_to,expires_at are enforced when referenced. Optional unresolved_issues[] contains nonempty strings and is retained.

Every field named source_ref or ending _source_ref must reference the registry. Missing/unregistered, audience-withheld, future-known, future-economic, expired or not-yet-effective evidence fails before calculation. These historical observation methods require source.as_of<=source.known_at<=knowledge_cutoff and source.as_of<=request.as_of. No source truth, license or approval authentication occurs.

Use decimal strings to preserve supplied digits; integers and finite JSON numbers are accepted by the shared Decimal reader. Booleans/null/nonfinite values are not numbers. Supported Decimal inputs have at most38 coefficient digits and exponent/adjusted exponent within+/-38; arithmetic outside the256-digit exact context fails. Domain ratios use explicit precision described below. Except where noted, domain row lists contain1..1000 entries and identifiers are unique. Extra input fields are included in the complete source hash but are not interpreted as instructions or domain facts.

Native output is the foundation envelope: contract_version,skill,request_id,object_id,as_of,knowledge_cutoff,currency,audience,status,draft=true,action_taken=false,human_review_required=true,delivery_status=not-delivered,method,results,unresolved_issues,limitations,handoffs,source_assurance=supplied-unverified,source_refs,input_hash,source_truth=unverified. No original input is embedded. Output validator requires detached original and rejects every altered/extra output field.

## Domain fields

events[]{event_id,type,record_date,position_date,payable_date,event_source_ref,position_source_ref,eligible_quantity,tolerance,received_amount?}. position_date must equal record_date<=as_of; payable_date>=record_date.

For cash_dividend add cash_per_share>=0 and withholding_rate in[0,1]. For stock_split add new_shares,old_shares positive integers and fractional_policy=preserve-entitlement. received_amount may be null/absent; when supplied add received_date and receipt_source_ref. For a split it is additional units, potentially negative for reverse split. For cash it is nonnegative net cash.

## Numerical precision

Cash arithmetic exact Decimal; stock-split ratio rounded to24 decimal places. Tolerance is supplied in cash or additional-security-unit measure as appropriate.

Actual period endpoints, received/recorded events and dated valuation observations must also be on or before the request as-of, knowledge cutoff and their own source known-at date. Earlier source metadata cannot validate a later completed observation. Contractual due/payable dates, validity expiries and prospective terms may remain future dated. These chronology checks validate supplied declarations only.
