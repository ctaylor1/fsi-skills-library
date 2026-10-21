# Phase 1 native contract — version0.2.0

Required: theme, as_of, config_version, sources and dimensions. sources carry unique source_id, tier1..4, strict date and optional url_ref. required_dimensions optionally selects from value_chain, competitors, customers, regulation, technology, economics, transactions and strategic_implications; default is the supplied dimension set. Findings use source_id and optional corroborating_source_ids. Competitors and revenue_share_pct are optional. Shares require an eligible cited source before concentration is computed.

Withhold findings without a nonfuture, nonstale tier1..3 source; a tier4 assertion alone cannot support inclusion. Preserve full source metadata and competitor source IDs. Compute CR4/CR8 and named-set HHI only on complete cited share inputs; otherwise concentration is null/not-evaluable. Report requested-dimension gaps and withheld findings as partial. Configured HHI bands are method descriptors, never jurisdictional competition rules.

All dates are strict YYYY-MM-DD calendar dates. JSON nonfinite values and booleans used as financial numbers fail validation. Malformed shapes return controlled validation errors. Source/date/permission facts remain caller declarations. Any complete label is limited to the declared supplied scope, never professional acceptance or authenticated source truth.

The public calculation and `validate` entrypoints remain available. Native results include `input_hash` over every supplied field and `source_truth: unverified`; no raw source snapshot is embedded. Output validation requires the detached original and reconstructs the full result, rejecting altered, omitted and extra fields. CLI: `python3 -B scripts/validate_output.py OUTPUT.json --input INPUT.json`. Narrative belongs in a separate reviewed artifact.

Version migration: retain original0.1 inputs as historical records; revise them to the explicit0.2 contract before recomputation. In particular sizing now requires dimensional declarations; qualitative landscape and unblended valuation are supported within their supplied scope. Existing source-bound envelopes require a reviewed adapter update, not silent schema conversion.
