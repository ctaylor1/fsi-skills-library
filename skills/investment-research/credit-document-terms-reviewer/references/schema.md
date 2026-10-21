# Native schema — 0.3.0

Require nonempty `doc_id`, `doc_type`, `issuer`, legal `issuer_id`, `instrument`, `instrument_id`, `doc_version`, `governing_law` and valid calendar `effective_date`. `expected_fields[]` uses supported field labels. Each candidate requires supported `field`, nonempty string `raw_value`, positive integer `page`, and nonempty string `locator`; optional confidence is a finite number in [0,1]. `is_amendment` is boolean when supplied. Amendment/supersession indicators are retained as unresolved context. Economic effective dates are not knowledge timestamps or evidence of source availability.

## Output and partial coverage

The extraction packet retains issuer/instrument identifiers and labels, document identity/version/governing-law assertions, raw candidates, normalized values, status, reasons and page/locator citations. `not_found` means no supplied candidate, not absence from the full document. Drafts, amended or superseding documents have their term values withheld with `needs_review` until a governing-document review occurs outside this normalizer.

All outputs include canonical `input_hash` over the complete original JSON and `source_truth: unverified`; no embedded `source_input` is accepted. Keep the original separately. Finite JSON, domain guards and input shape validation run before computation. Output validation requires `--input` (self-test retains its fixture original) and reconstructs every native field. Added narrative is a separate reviewed artifact, not a permitted unchecked field.

Negated or qualified seniority remains needs_review. Floating coupons normalize a supplied positive additive spread in basis points or percentage points (2.50% = 250 bps); missing index or spread remains needs_review. This does not calculate reset coupons, floors, caps or contractual interest.
