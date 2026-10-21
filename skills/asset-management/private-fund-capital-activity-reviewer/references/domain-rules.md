# Bounded method

Closing unfunded=opening+explicit increases-explicit decreases. Track calls and distributions independently; net cash to LP=distributions-calls. Compare reported closing minus calculated closing; no silent balancing item. Calls cannot increase unfunded; distributions cannot reduce unfunded. Mixed/missing currency, future events, unavailable source or unknown amount withhold the complete rollforward; known cash subtotals remain explicitly partial. No implicit recallability from a distribution label.

Required common fields: request_id, object_id, as_of, knowledge_cutoff, currency (one ISO-style currency), audience=internal-review, sources[{source_ref,version,as_of,known_at}]. Source ids are unique. Optional source permitted_audiences, valid_from, valid_to, expires_at and approval_status constrain eligibility. Each business row/source reference must resolve. Sources known after knowledge_cutoff reject the request. Dates use YYYY-MM-DD. All financial facts are supplied declarations, not authenticated extraction. Retain original input separately; native output forbids source_input.

Numeric inputs: finite decimal strings recommended; <=38 coefficient digits, exponent and adjusted exponent +/-38, <=256 literal characters. Arithmetic uses a private precision256 Decimal context; ratios explicitly round to12 places. No infinities, boolean amounts or implicit zero filling. Keep jobs bounded (<=100,000 rows per collection); split larger populations with stable identifiers and separately reconciled totals. Unknown value=null produces a gap or explicit unsupported operation. Every source must be permissioned for the internal reviewer. Numeric results and classifications remain draft only.

## Failure handling

Invalid shape, duplicate business identifiers, unsupported numeric magnitude and impossible arithmetic fail closed. Insufficient evidence produces unresolved issues and withheld dependent results. A no-exception result covers only supplied scope and does not imply professional acceptance.
