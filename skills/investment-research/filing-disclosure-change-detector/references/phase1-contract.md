# Phase 1 native contract — version0.2.0

Required: issuer, as_of, prior/current{form_type,filing_date,sections}. Section IDs and exhibit numbers must be unique. Dates must be valid, current cannot predate prior and neither filing may postdate the knowledge cutoff. Omitted exhibits on either side make exhibit comparison not evaluable; explicit empty inventories are distinct. sections_complete=false withholds absence-based structural findings. Missing comparable text is not evaluable.

Compare aligned sections, risk tags and supplied exhibit hashes/descriptions. Detect restatement markers only when the marker set changes from the prior section; quote the actual marker location. Type-based review lanes are not materiality scores. coverage_status applies to supplied inventories only, not extraction completeness.

All dates are strict YYYY-MM-DD calendar dates. JSON nonfinite values and booleans used as financial numbers fail validation. Malformed shapes return controlled validation errors. Source/date/permission facts remain caller declarations. Any complete label is limited to the declared supplied scope, never professional acceptance or authenticated source truth.

The public calculation and `validate` entrypoints remain available. Native results include `input_hash` over every supplied field and `source_truth: unverified`; no raw source snapshot is embedded. Output validation requires the detached original and reconstructs the full result, rejecting altered, omitted and extra fields. CLI: `python3 -B scripts/validate_output.py OUTPUT.json --input INPUT.json`. Narrative belongs in a separate reviewed artifact.

Version migration: retain original0.1 inputs as historical records; revise them to the explicit0.2 contract before recomputation. In particular sizing now requires dimensional declarations; qualitative landscape and unblended valuation are supported within their supplied scope. Existing source-bound envelopes require a reviewed adapter update, not silent schema conversion.
