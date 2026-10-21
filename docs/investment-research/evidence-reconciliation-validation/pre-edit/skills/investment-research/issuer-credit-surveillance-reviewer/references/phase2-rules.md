# Method and limitations

Compare source-bound reported current and prior EBITDA ratios, interest coverage and liquidity against matching accounting/currency/scope. Periods ending after economic as-of are rejected rather than treated as reported performance. Change alerts use supplied thresholds. Fixed-charge EBITDA less capex divided by interest is a proxy, never DSCR or covenant compliance.

Spread differences require exact security,currency,basis matching and the observation chronology, cutoff, source-knowledge and explicit current-age rules in [the schema](phase2-schema.md). Compare timestamp instants in UTC without truncation; use UTC calendar dates solely for the separate economic as-of check. Never infer a quote observation from its source publication time or a missing timestamp. Withhold an ineligible comparison and its widening alert while retaining supported financial metrics. The source permission/cutoff gate can still withhold the entire analytical projection.

Ratings remain reported agency assertions. No rating/position/thesis action is taken. The legacy Phase 1 contract remains supported without schema_version; these analytical changes do not rebaseline its earlier validation evidence.

Software checks establish finite arithmetic and exact reconstruction only. Domain, legal and institutional acceptance remain not established.
