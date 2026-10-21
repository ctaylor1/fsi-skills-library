# Native contract

Required common fields: request_id,object_id nonempty strings; as_of and knowledge_cutoff real YYYY-MM-DD; currency three uppercase letters (provider nonmonetary mode may use not-applicable); audience=internal-review; sources[] nonempty (maximum100000) with unique source_ref,version,as_of,known_at. Optional source permitted_audiences,valid_from,valid_to,expires_at are enforced when referenced. Optional unresolved_issues[] contains nonempty strings and is retained.

Every field named source_ref or ending _source_ref must reference the registry. Missing/unregistered, audience-withheld, future-known, future-economic, expired or not-yet-effective evidence fails before calculation. These historical observation methods require source.as_of<=source.known_at<=knowledge_cutoff and source.as_of<=request.as_of. No source truth, license or approval authentication occurs.

Use decimal strings to preserve supplied digits; integers and finite JSON numbers are accepted by the shared Decimal reader. Booleans/null/nonfinite values are not numbers. Supported Decimal inputs have at most38 coefficient digits and exponent/adjusted exponent within+/-38; arithmetic outside the256-digit exact context fails. Domain ratios use explicit precision described below. Except where noted, domain row lists contain1..1000 entries and identifiers are unique. Extra input fields are included in the complete source hash but are not interpreted as instructions or domain facts.

Native output is the foundation envelope: contract_version,skill,request_id,object_id,as_of,knowledge_cutoff,currency,audience,status,draft=true,action_taken=false,human_review_required=true,delivery_status=not-delivered,method,results,unresolved_issues,limitations,handoffs,source_assurance=supplied-unverified,source_refs,input_hash,source_truth=unverified. No original input is embedded. Output validator requires detached original and rejects every altered/extra output field.

## Domain fields

`basket_control`: direction=creation/redemption; creation_unit_size,creation_units positive integers; cash_per_creation_unit signed; transaction_fee>=0,value_tolerance>=0; basket_source_ref,nav_source_ref,ap_source_ref,dealing_terms_source_ref; order_received_at,cutoff_at aware timestamps; ap_status=supplied-active/unknown/expired; ap_valid_until; basket_type=standard/custom; nav_per_share positive or null. Custom adds custom_review_status=supplied-approved/pending/unknown and custom_review_source_ref. components[]{instrument_id,quantity_per_creation_unit>=0,price positive or null,source_ref}; empty list is cash-only.

`secondary_market`: nav_per_share,market_price,bid,ask all positive with bid<=ask; nav_source_ref,quote_source_ref,nav_date,quote_date, both dates equal as_of.

## Numerical precision

Basket/cash/quantity arithmetic exact Decimal; secondary-market ratios round to12 decimal places. Per-creation-unit tolerance excludes transaction fees.

Actual period endpoints, received/recorded events and dated valuation observations must also be on or before the request as-of, knowledge cutoff and their own source known-at date. Earlier source metadata cannot validate a later completed observation. Contractual due/payable dates, validity expiries and prospective terms may remain future dated. These chronology checks validate supplied declarations only.

For basket_control, basket_source_ref identifies the supplied order/basket packet and bounds the actual order_received_at date. Supplied component prices and NAV are observations for request as_of; an earlier evidence date must not be relabeled as a current quote. Missing prices/NAV remain unavailable.
