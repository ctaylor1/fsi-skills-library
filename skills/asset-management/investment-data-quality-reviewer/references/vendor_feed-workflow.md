# Cross-source investment data comparison

Compare supplied internal and vendor observations at instrument/domain/field grain, preserving independent stale and value findings and withholding incompatible currency, unit or time comparisons.

## Workflow

1. Establish the named portfolio/fund, dates, source access, responsible reviewer and applicable policy. This development package has not received institutional acceptance.
2. Read [native schema](vendor_feed-schema.md) and [bounded method](vendor_feed-domain-rules.md). Obtain actual source fields; preserve missingness and unresolved upstream issues.
3. Run `python3 -B scripts/vendor_feed_validate_input.py INPUT.json`, then `python3 -B scripts/vendor_feed_calculate_or_transform.py INPUT.json`. These offline utilities use supplied JSON; no live connector or source authentication is bundled.
4. Validate the immutable result with `python3 -B scripts/vendor_feed_validate_output.py OUTPUT.json --input INPUT.json`. Keep the retained input separate from outputs and downstream audiences. Source hashes establish reproducibility, not factual correctness, source authentication or authority.
5. Review exceptions and unknowns with the accountable professional. Write any narrative as a separate reviewed artifact; the native validator accepts only the computed schema. Apply [controls](vendor_feed-controls.md) and [handoff boundaries](vendor_feed-handoffs.md).

## Sources and operation

Use [source-map](vendor_feed-source-map.md) for provenance requirements. Required enterprise integrations are deployment prerequisites, not installed capabilities. Jurisdiction metadata does not create applicable legal rules. Thresholds and synthetic fixtures are development conventions requiring target-specific review.

The eval manifest contains executable regression checks and declarative workflow/routing cases. Software checks establish bounded behavior only; natural-language quality, independent specialist review, audience isolation and deployment acceptance remain separate gates.
