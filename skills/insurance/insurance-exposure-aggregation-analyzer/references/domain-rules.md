# Native domain method and limits

The unit of aggregation is one insured policy/location record at the valuation date. Duplicate row IDs or duplicate policy/location identities invalidate totals, even when amounts agree. Resolve endorsements, split coverages and overlapping schedules upstream into the reviewed unique-record grain; the helper never silently keeps the first row. The sum describes insured schedule TIV across policies, not unique physical property value. Location IDs may recur across policies, but do not interpret that grouping as a deduplicated asset valuation.

Totals remain separated by currency. Account and location partitions reconcile to each currency total. A location may carry several perils: each peril slice includes its full supplied TIV, so peril slices overlap and must never be summed into a portfolio total. No currency conversion, limit, deductible, coinsurance, business-interruption inference, geographic enrichment, geocoding or catastrophe calculation is performed.

Known TIV may remain reportable while geocode/model quality is incomplete. Rooftop or street geocodes with valid latitude/longitude and an accepted supplied model-quality/version assertion avoid the local quality finding; this is a reviewed-input convention, not model approval. Missing, postcode-only or out-of-range geocodes and limited/unknown model quality stay in the quality register and make the overall evidence partial. Missing values, basis, source or identity withhold totals; these are different from a known zero TIV.

ASOP 23 informs review and disclosure of supplied-data limitations; it does not make this synthetic check an audit. ASOP 38 informs model suitability and reliance documentation. Neither supplies a legal underwriting or model-acceptance rule.
