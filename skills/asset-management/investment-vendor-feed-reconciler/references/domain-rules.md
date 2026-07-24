# Domain Rules - investment-vendor-feed-reconciler

Deterministic internal-vs-vendor market-data reconciliation: how field-level observations are
matched, how disagreements are classified into a fixed **break taxonomy**, how the result **ties
out** by completeness, and how each break is **routed** (never resolved). Tolerances, materiality,
staleness, and routing are configuration (versioned, owned by market-data governance), not
hard-coded judgments.

## Matching (deterministic, cell by cell)

A **cell** is one `(instrument_id, domain, field)` triple. Internal and vendor observations are
indexed by cell; the union of cells is reconciled. For each cell present on **both** sides:

- **Numeric** (both values parse as numbers and neither declares `data_type: "categorical"`):
  agree when `abs(internal - vendor) <= max(numeric_tolerance_abs, numeric_tolerance_pct * max(|a|,|b|))`.
- **Categorical** (otherwise, e.g. ratings, identifiers, dates, `member` flags): agree when the
  trimmed, upper-cased strings are equal.
- If the values agree but **either side's `as_of` is older than `staleness_max_age_days`** before
  the job cutoff, the cell is a `stale_as_of` break, not a match.

Cells present on **only one** side are `missing_in_vendor` (internal-only) or `missing_in_internal`
(vendor-only).

## Break taxonomy

| Break type | Fires when | Key evidence | Default routing |
| ---------- | ---------- | ------------ | --------------- |
| `value_mismatch` | Both sides have the field but the values disagree beyond tolerance | signed numeric `difference` (numeric) or both raw values (categorical) | by domain (below) |
| `missing_in_internal` | Field present in the vendor feed, absent internally | vendor value + as-of | by domain |
| `missing_in_vendor` | Field present internally, absent in the vendor feed | internal value + as-of | by domain |
| `stale_as_of` | Values agree but a source's as-of is older than the staleness threshold | `as_of_gap_days` | by domain |

Every break carries `material` (categorical mismatches and missing cells are material; a numeric
mismatch is material when the relative move `>= materiality_pct` or the absolute move
`>= materiality_abs`; `stale_as_of` is informational/non-material), full `lineage`, a `route`, a
`disposition` (`UNRESOLVED`), and `canonical_value: null`.

## Domain routing (evidence forwarded, never resolved)

| Domain | Route |
| ------ | ----- |
| `price` | `valuation-exception-packet` (mandatory - all price discrepancies incl. stale prices) |
| `rating`, `instrument_attribute` | `security-master-enricher` (reference-data enrichment proposal) |
| `corporate_action` | `corporate-action-interpreter` (interpret authoritative event terms) |
| `index_constituent` | index/benchmark data owner (human review) |

## Tie-out invariants (enforced by `scripts/validate_output.py`)

1. **Completeness:** `matched_cells + break_cells == total_cells` (the union of cells on either
   side); `residual_cells == 0`. No cell is dropped or double-counted. If it does not complete,
   the reconciliation fails closed.
2. `break_cells == len(breaks)` and `internal_cells` / `vendor_cells` are consistent with the
   union.
3. Every break's `type` is in the taxonomy and carries `instrument_id`, `domain`, `field`,
   `material`, and per-source `as_of` times.
4. Every price-domain break routes to `valuation-exception-packet`.

## Idempotency, durable IDs & lineage

- `input_fingerprint` = SHA-256 of the normalized inputs + config.
- `reconciliation_id` = `ivfr-{entity}-{as_of}-{fingerprint[:8]}`. It has **no timestamp or random
  component**, so identical inputs reproduce an identical reconciliation; this id is the durable
  handle downstream owners cite.
- `break_id` = `BRK-NNNN`, stable in sorted `(instrument_id, domain, field)` order. Every break
  traces to its internal/vendor source rows via `lineage` citations carrying as-of times.

## Version & effective-date rules

- Tolerances, materiality, staleness, and routing come **only** from the versioned `config`; the
  output records `config_version`. They are never tuned per-run to make a break disappear.
- The firm's reference-data / pricing hierarchy policy is a versioned document used to **route**
  and to label lineage; it is never applied by this skill to select a value.
- A vendor feed's own effective/publish dating is preserved in each observation's `as_of` and
  drives staleness; the job `as_of` is the reconciliation cutoff.

## Hard boundaries (fail closed)

- **Never choose the canonical value.** The skill does not select, prefer, average, or write a
  "golden"/canonical value; every break stays `UNRESOLVED` with `canonical_value: null`.
- **Never repair or override a record.** It emits no correction, no overwrite, no security-master
  write. Discrepancies are surfaced and routed for authorized humans/downstream skills.
- **Never suppress a discrepancy** to force a tie; the completeness tie-out must hold on the real
  breaks.
- **Route price exceptions to `valuation-exception-packet`**; do not adjudicate a price here.
- **No investment advice** and no directive to buy/sell/rebalance from a discrepancy.
