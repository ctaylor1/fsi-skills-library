# Bounded method

Use an aggregate LP pool, without GP invested-capital participation. Tier1 pays min(cash, unreturned LP capital) to LPs. Tier2 pays min(remaining cash, supplied accrued preferred entitlement) to LPs. Tier3 pays carry_fraction of remaining cash to GP and the remainder to LPs. Sum tiers and verify distributable cash-LP total-GP total=0. Show capital/preference unpaid after the distribution. Preferred accrual is supplied, never inferred from elapsed time or a headline hurdle. Contract-specific state must already reflect prior distributions and be independently reviewed.

Required common fields: request_id, object_id, as_of, knowledge_cutoff, currency (one ISO-style currency), audience=internal-review, sources[{source_ref,version,as_of,known_at}]. Source ids are unique. Optional source permitted_audiences, valid_from, valid_to, expires_at and approval_status constrain eligibility. Each business row/source reference must resolve. Sources known after knowledge_cutoff reject the request. Dates use YYYY-MM-DD. All financial facts are supplied declarations, not authenticated extraction. Retain original input separately; native output forbids source_input.

Numeric inputs: finite decimal strings recommended; <=38 coefficient digits, exponent and adjusted exponent +/-38, <=256 literal characters. Arithmetic uses a private precision256 Decimal context; ratios explicitly round to12 places. No infinities, boolean amounts or implicit zero filling. Keep jobs bounded (<=100,000 rows per collection); split larger populations with stable identifiers and separately reconciled totals. Unknown value=null produces a gap or explicit unsupported operation. Every source must be permissioned for the internal reviewer. Numeric results and classifications remain draft only.

## Failure handling

Invalid shape, duplicate business identifiers, unsupported numeric magnitude and impossible arithmetic fail closed. Insufficient evidence produces unresolved issues and withheld dependent results. A no-exception result covers only supplied scope and does not imply professional acceptance.
