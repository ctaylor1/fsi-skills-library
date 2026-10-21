# Phase 1 native contract — version0.2.0

Required: config_version, profile_id, company{company_id,legal_name}, as_of_date, required_sections, facts. Each fact has section/fact_id and needs source_ref, company_id and effective_date before inclusion; expires and available_at bound eligibility. Missing evidence yields a withheld open item. Only included facts enter content sections. External-profile restricted facts omit their value, title and source locator. Approvals are unverified supplied records, never clearance.

Confirm issuer identity, strict calendar dates, requested sections and distribution. Include only sourced, matching, current and available facts; retain generic restricted exclusions and explicit missing sections. coverage_status is partial while open items exist.

All dates are strict YYYY-MM-DD calendar dates. JSON nonfinite values and booleans used as financial numbers fail validation. Malformed shapes return controlled validation errors. Source/date/permission facts remain caller declarations. Any complete label is limited to the declared supplied scope, never professional acceptance or authenticated source truth.

The public calculation and `validate` entrypoints remain available. Native results include `input_hash` over every supplied field and `source_truth: unverified`; no raw source snapshot is embedded. Output validation requires the detached original and reconstructs the full result, rejecting altered, omitted and extra fields. CLI: `python3 -B scripts/validate_output.py OUTPUT.json --input INPUT.json`. Narrative belongs in a separate reviewed artifact.

Version migration: retain original0.1 inputs as historical records; revise them to the explicit0.2 contract before recomputation. In particular sizing now requires dimensional declarations; qualitative landscape and unblended valuation are supported within their supplied scope. Existing source-bound envelopes require a reviewed adapter update, not silent schema conversion.

Financial/ownership/trading fact values must be scalar text or finite numbers; booleans and nonfinite tokens are invalid financial values. Missing/blank values remain withheld open items rather than asserted facts. Nonfinancial boolean assertions may remain typed supplied facts.
