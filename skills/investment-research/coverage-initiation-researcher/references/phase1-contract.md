# Phase 1 native contract — version0.2.0

Required: ticker, company_name, as_of, analyst_id, config_version, sections, forecast and valuation. Sections contain supplied text/citations; forecast has ascending years and positive revenue, with optional signed EBIT margins and cited assumptions. Valuation methods have unique IDs and finite per-share values. weights are optional; when explicitly supplied, they must be nonnegative, cover methods and sum to one. A cited method can be complete without a blend. Retain claims and forecast_snapshot in the result.

Grade supplied section coverage, recompute revenue growth, apply only explicitly configured margin bounds and show the supplied valuation range. Negative margins are valid by default. Missing methods/claims or absent MNPI attestation prevent readiness. A weighted midpoint is optional arithmetic, not a prescribed valuation reconciliation or target.

All dates are strict YYYY-MM-DD calendar dates. JSON nonfinite values and booleans used as financial numbers fail validation. Malformed shapes return controlled validation errors. Source/date/permission facts remain caller declarations. Any complete label is limited to the declared supplied scope, never professional acceptance or authenticated source truth.

The public calculation and `validate` entrypoints remain available. Native results include `input_hash` over every supplied field and `source_truth: unverified`; no raw source snapshot is embedded. Output validation requires the detached original and reconstructs the full result, rejecting altered, omitted and extra fields. CLI: `python3 -B scripts/validate_output.py OUTPUT.json --input INPUT.json`. Narrative belongs in a separate reviewed artifact.

Version migration: retain original0.1 inputs as historical records; revise them to the explicit0.2 contract before recomputation. In particular sizing now requires dimensional declarations; qualitative landscape and unblended valuation are supported within their supplied scope. Existing source-bound envelopes require a reviewed adapter update, not silent schema conversion.
