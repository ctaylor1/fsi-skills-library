# Implemented method and limits

The only live implementation is the supplied-evidence method described in [analytical rules](phase2-rules.md) and [schema](phase2-schema.md). It compares source-bound corporate reported leverage, interest coverage, a fixed-charge proxy, supplied available liquidity to known maturities, eligible spread observations and reported events.

Gross/net debt-to-EBITDA requires positive EBITDA; coverage requires positive interest. The fixed-charge measure is `(EBITDA - mandatory_capex) / interest_expense`, not contractual FCCR or DSCR. The liquidity measure is `(unrestricted_cash + available_committed_facilities) / near_term_maturities`, requiring positive maturities and a supplied complete inventory. It does not assess all operating/contingent uses, restricted cash, refinancing feasibility or funding access. Obtain a separately validated capital-structure/maturity method when instrument-level maturity detail is required.

Financial observations must use comparable duration, fiscal calendar, currency, units, accounting basis and consolidation scope and end no later than economic as-of and the cutoff date. Source knowledge is separate from economic period. No forecast/scenario or specialist bank/insurer conversion is inferred.

Source-bound quotes require the observation, mapping and freshness controls in the analytical schema; a current source timestamp cannot date an unknown quote. Missing/inconsistent evidence withholds dependent measures. Full reconstruction detects changed/extra/removed output or a substituted original. Source assertions and hashes do not authenticate facts, licensed use or professional approval.

The legacy packet assembly is retired. Use [reviewed migration](schema.md); do not execute historical source as a production fallback or reinterpret old success fixtures as current eligibility evidence.
