# Phase 1 native contract — version0.2.0

Required: doc_a/doc_b{doc_id,version,sections}; matching document IDs and unique nonempty section IDs. Each section may supply heading, text and values maps. Missing text or a one-sided omitted value inventory is not evaluable. extraction_complete must be boolean when supplied. A complete-for-declared-extracted-scope result requires both affirmative declarations and no missing comparable surface; those declarations are not verified.

Compare exact supplied text, headings, common-section order and explicit value fields; identify sections added/removed within the supplied inventories. No detected changes with incomplete extraction is partial-no-detected-change, never an unqualified clean result. Formatting, OCR/table extraction, formulas, legal and investment materiality are unsupported.

All dates are strict YYYY-MM-DD calendar dates. JSON nonfinite values and booleans used as financial numbers fail validation. Malformed shapes return controlled validation errors. Source/date/permission facts remain caller declarations. Any complete label is limited to the declared supplied scope, never professional acceptance or authenticated source truth.

The public calculation and `validate` entrypoints remain available. Native results include `input_hash` over every supplied field and `source_truth: unverified`; no raw source snapshot is embedded. Output validation requires the detached original and reconstructs the full result, rejecting altered, omitted and extra fields. CLI: `python3 -B scripts/validate_output.py OUTPUT.json --input INPUT.json`. Narrative belongs in a separate reviewed artifact.

Version migration: retain original0.1 inputs as historical records; revise them to the explicit0.2 contract before recomputation. In particular sizing now requires dimensional declarations; qualitative landscape and unblended valuation are supported within their supplied scope. Existing source-bound envelopes require a reviewed adapter update, not silent schema conversion.
