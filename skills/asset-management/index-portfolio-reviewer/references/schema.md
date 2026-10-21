# Native contract

Required common fields: request_id,object_id nonempty strings; as_of and knowledge_cutoff real YYYY-MM-DD; currency three uppercase letters (provider nonmonetary mode may use not-applicable); audience=internal-review; sources[] nonempty (maximum100000) with unique source_ref,version,as_of,known_at. Optional source permitted_audiences,valid_from,valid_to,expires_at are enforced when referenced. Optional unresolved_issues[] contains nonempty strings and is retained.

Every field named source_ref or ending _source_ref must reference the registry. Missing/unregistered, audience-withheld, future-known, future-economic, expired or not-yet-effective evidence fails before calculation. These historical observation methods require source.as_of<=source.known_at<=knowledge_cutoff and source.as_of<=request.as_of. No source truth, license or approval authentication occurs.

Use decimal strings to preserve supplied digits; integers and finite JSON numbers are accepted by the shared Decimal reader. Booleans/null/nonfinite values are not numbers. Supported Decimal inputs have at most38 coefficient digits and exponent/adjusted exponent within+/-38; arithmetic outside the256-digit exact context fails. Domain ratios use explicit precision described below. Except where noted, domain row lists contain1..1000 entries and identifiers are unique. Extra input fields are included in the complete source hash but are not interpreted as instructions or domain facts.

Native output is the foundation envelope: contract_version,skill,request_id,object_id,as_of,knowledge_cutoff,currency,audience,status,draft=true,action_taken=false,human_review_required=true,delivery_status=not-delivered,method,results,unresolved_issues,limitations,handoffs,source_assurance=supplied-unverified,source_refs,input_hash,source_truth=unverified. No original input is embedded. Output validator requires detached original and rejects every altered/extra output field.

## Domain fields

`tracking`: benchmark_id,portfolio_return_basis,benchmark_return_basis,frequency=daily/weekly/monthly/quarterly,aligned_periods_confirmed=true; periods[]{start,end,portfolio_return,benchmark_return,portfolio_source_ref,benchmark_source_ref}. Ordered contiguous historical periods; returns in[-1,10]. Supported calendar-day spans: daily1..7,weekly5..9,monthly27..32,quarterly80..100; practitioner must verify actual calendar/alignment. Annualization factors252,52,12,4.

`weights`: complete_union_including_cash=true; weights[]{instrument_id,portfolio_weight,benchmark_weight,source_ref}. Unique identifiers; each weight in[0,1]; each full column sums exactly1. Absence is not inferred as zero; include explicit zero weights.

## Numerical precision

Linked factors and means24 decimal places; sample variance48; square root128-digit context; reported tracking error24. Weight sums/products exact Decimal.

Actual period endpoints, received/recorded events and dated valuation observations must also be on or before the request as-of, knowledge cutoff and their own source known-at date. Earlier source metadata cannot validate a later completed observation. Contractual due/payable dates, validity expiries and prospective terms may remain future dated. These chronology checks validate supplied declarations only.
