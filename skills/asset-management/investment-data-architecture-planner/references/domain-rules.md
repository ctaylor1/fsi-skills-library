# Investment data decisions and bounded method

## Grain and authority

Agree whether the product contains an instrument attribute, security observation, position, account balance, benchmark membership/weight or portfolio aggregate before joining. A portfolio plus security is insufficient for a lot/account-level position unless the approved aggregation is separately defined. Account, security and benchmark identifiers from different namespaces never match merely because their raw text is equal. The local sample supports exact supplied identities only; no probabilistic match, deduplication of economic positions or crosswalk is inferred.

For each semantic field, retain its original unit/currency, source system/field, transformation and version. Distinguish price from value, decimal returns from percent, local from base currency and units from notional. Treat coupon/accrual conventions, corporate actions, derivatives identifiers, FX fixes, cash timing and valuation policies as owned requirements. The local method does not calculate these conventions or silently convert them. Take materially incompatible records to the relevant reference-data, exposure, performance or accounting owner.

Decide explicitly whether a benchmark feed represents an announced future membership, contemporaneously known membership or later vendor restatement. Keep benchmark version, valuation date and point-in-time availability in the contract. Do not use a current constituent set to claim a historical research universe. Separate accounting book finality from investment book timeliness and identify the reconciliation owner.

## Temporal resolution

Each row supplies business-valid `[valid_from, valid_to)` and institution-known `[known_from, known_to)` intervals. Endpoints are dates, so the implementation supports daily resolution only; intraday evidence needs a separately approved timestamp method. A late correction closes the old known interval and starts a new assertion at the correction's known date. This preserves what was known before correction. Multiple active assertions are ambiguous even if their values happen to agree. The output lists all candidates and withholds the selected value; correction precedence needs explicit source evidence and a new input.

The test example has value 100.25 valid September 1, known September 2–19, and a corrected 101.75 known from September 20. A September 10 replay yields 100.25; a September 20 replay yields 101.75. Neither illustrates actual prices or investments. Complete sample evidence does not prove the producer supplied its complete population.

## Access and operation

The offline adapter checks a license and current-date permission declaration for the exact dataset/principal/purpose/audience/read operation. A passed declaration only permits evaluation of the supplied local sample; it never authorizes a connection. Access issues withhold sample values. Shared architecture issues and inherited scope issues also withhold dependent values. Source-level audience restrictions fail before computing the draft.

The separate gateway client performs actual read-time permission checks only against an institution-approved HTTPS gateway and protected deployment policy. Keep gateway identity, license interpretation, entitlements and data truth as distinct assurances. For a saved record, record its original locator/version and observed time, then treat it as unverified historical evidence. No offline JSON flag proves a live permission.

Observability compares a supplied observed number to its declared threshold using exact decimal comparisons; it never compares a projected number as observed. Design the operational controls around freshness, completeness, duplicate/late arrivals, correction volume, permission failures and unavailable upstreams. The narrow local monitor contract accepts supplied metrics; it does not run a scheduler, collect live telemetry or guarantee coverage. Specify which dependent valuations/research outputs must be held, replayed or reviewed after a failure.
