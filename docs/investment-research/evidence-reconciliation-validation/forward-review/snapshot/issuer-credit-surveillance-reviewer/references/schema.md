# Native schema — 0.2.0

Require packet/config versions, `issuer{issuer_id,name,sector,as_of}`, aware intraday `knowledge_cutoff`, source registry, financials, maturity rows, spreads object, ratings/covenant arrays and approval records. Financials and any prior financials require issuer, currency, units, period, accounting basis, a filing/company `source_id`, and numeric EBITDA, gross debt, cash, interest expense, capex and undrawn revolver. Prior currency/units/accounting basis must match. All financial amounts except EBITDA are nonnegative. Registry sources require source ID, type, reference and aware `known_at` no later than cutoff; external eligibility is a boolean assertion. Economic period/as_of remains separate from knowledge time.

## Output and partial coverage

Packet sections, metrics, basis, source assertions, tie-outs, changes, source-linked maturity/instrument detail, reported rating object identity, covenant instrument/document/version, flags, approvals and unresolved issues are retained. `support_status` is `PARTIAL` for unresolved data/review gates, otherwise `SUPPLIED_INPUT_REVIEW`. Neither means institutional acceptance. A faithful partial can pass reconstruction while its data/review gates stay held. Action fields remain reported-only / none / unchanged.

All outputs include canonical `input_hash` over the complete original JSON and `source_truth: unverified`; no embedded `source_input` is accepted. Keep the original separately. Finite JSON, domain guards and input shape validation run before computation. Output validation requires `--input` (self-test retains its fixture original) and reconstructs every native field. Added narrative is a separate reviewed artifact, not a permitted unchecked field.
