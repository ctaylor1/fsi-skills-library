# Supported update method

Canonical input hashing uses sorted JSON object keys, compact separators, Unicode
preservation and finite numbers. Compare the supplied original hash and observed
current version/hash before building any proposal. A mismatch requires rebase and
review against a newly retained original; there is no automatic conflict merge.

Three-statement replacements are restricted to existing numeric historical income
statement/balance sheet fields, `historical.year`, `forecast_years`, recognized
driver values/source text, and base/upside/downside growth or margin deltas beneath
`model_input`. Driver source text changes require their own cited patch. The
package never infers or silently replaces provenance text when a driver changes.

DCF replacements are restricted to `wacc`, `terminal_growth`, `diluted_shares`,
`discounting`, named EV-to-equity bridge values and existing indexed forecast row
financial values/year/period dates. Changing a share count cannot change security,
share class or share-count basis. Forecast row identities/basis are immutable.
Input rows cannot be appended, removed or reordered by this bounded version.

Only financial numeric scalars, supported calendar dates, discounting values and
source text may be replaced. No identity, currency, unit, accounting basis,
consolidation, configuration, rights, approval or execution field is patchable.
Period roll-forward uses explicit period/date patches with the same row inventory;
it does not invent newly reported historical statements or automatically close a
period. The actual native model must check financial identities, forecast-year
continuity, domain ranges and funding feasibility after staging.

A draft is not a validated rebuilt model. Use the reviewed handoff to the declared
native model to execute its real input validator, compute and original-bound
output validator. For example, changing annual growth from 10% to 12% against a
retained revenue of 1,000 produces a staged growth input; the actual three-statement
engine, not this package, produces first-year revenue of 1,120 and linked cash.
Native tie-outs, economic review and human approval remain separate.

The retained original must also have eligible evidence at its own recorded context;
a source learned after its cutoff cannot be backfilled into the old snapshot just
because it is eligible now. Newly learned evidence belongs to explicit current
patches with a distinct source record.

Source metadata and the observed current hash are supplied assertions. Keeping
an old source record preserves provenance but can make a proposal ineligible when
that source has expired or its rights are unavailable at `use_on`; resolve this
under institution controls rather than rewriting old entitlements in place.
