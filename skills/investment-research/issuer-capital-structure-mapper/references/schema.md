# Native schema — 0.2.0

`company{company_id,name,as_of}` uses a calendar economic as-of date. `instruments[]` is nonempty. Each row requires durable `instrument_id`, legal `issuer_id`, explicit three-letter `currency` and `source_ref`. Principal and coupon are finite nonnegative JSON numbers or null. `secured` is boolean or null; `maturity_date` is a valid calendar date or null. Supplied type and seniority are descriptive labels, not a legal determination.

## Output and partial coverage

`instruments[]` retains identity, amount, currency, coupon, maturity, security assertion and source reference. `by_currency` holds each currency inventory and coverage flags. A single-currency packet exposes those fields at the top level; mixed-currency top-level totals and averages are null. `total_debt` is null if principal coverage is incomplete; `known_principal` is a labeled subtotal. Unknown maturity uses an `undated` bucket and withholds full WAM and near-term totals. Unknown coupon withholds full WAC; separately labeled known-subset averages retain their own denominators. Missing principal stays in detail and `excluded_instruments`.

All outputs include canonical `input_hash` over the complete original JSON and `source_truth: unverified`; no embedded `source_input` is accepted. Keep the original separately. Finite JSON, domain guards and input shape validation run before computation. Output validation requires `--input` (self-test retains its fixture original) and reconstructs every native field. Added narrative is a separate reviewed artifact, not a permitted unchecked field.
