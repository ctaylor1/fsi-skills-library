# Controls - investment-vendor-feed-reconciler

- **Risk tier:** R2 - analytical / drafting. **Action mode:** Draft-only; no system-of-record
  change.
- **Human approval:** `external-delivery` - required before the discrepancy pack is delivered
  externally or written to a system of record. Internal analytical use may be reviewer-sampled.

## Prohibited (fail closed)

- **No canonical selection.** The skill never chooses, prefers, averages, or writes a
  "golden"/canonical value for any field. Every break carries `canonical_value: null` and
  `disposition: "UNRESOLVED"`. Choosing the canonical value is the HARD BOUNDARY.
- **No repair / override.** No overwrite of the internal book, no security-master write, no vendor
  correction, no record repair. Discrepancies are surfaced and routed only.
- **No adjudication.** The skill does not decide which source is "correct" or authoritative.
- **No forced tie / no suppression.** No dropping or netting of cells to make the feed appear to
  agree; the completeness tie-out must hold on the real breaks.
- **No per-run threshold tuning.** Tolerances, materiality, staleness, and routing come only from
  the versioned `config`.
- **No investment advice / no trade or rebalance directive** implied by a discrepancy.

## Required output screens (`scripts/validate_output.py`)

- **Tie-out (completeness):** `matched_cells + break_cells == total_cells`; `residual_cells == 0`;
  `ties_out == true`; `break_cells == len(breaks)`.
- **Break taxonomy:** every break's `type` is in {`value_mismatch`, `missing_in_internal`,
  `missing_in_vendor`, `stale_as_of`} with `instrument_id`, `domain`, `field`, `material`.
- **Lineage & as-of:** every break cites its source rows (`internal:` / `vendor:` prefix), each
  citation carries an `@as-of` time, and each cited side surfaces its `as_of`.
- **Idempotency:** `reconciliation_id` derived from `entity/as_of/input_fingerprint` with no
  timestamp/random component; `input_fingerprint` is a 64-hex content hash.
- **No-adjudication / never-repaired (R2 prohibited-decision screen):** every break has
  `canonical_value == null` and a non-binding `disposition`; price-domain breaks route to
  `valuation-exception-packet`; a language screen blocks chosen-value / override / repair / advice
  phrasing.
- **Disclaimer:** the standing no-adjudication disclaimer is present.

## Segregation of duties

- The skill **classifies and routes** discrepancies. A different, authorized human or downstream
  skill **investigates, decides the canonical value, and (if warranted) writes the record** under
  the firm's data-governance controls. Detection and adjudication must not be the same actor.

## Data classification, privacy, records

- **Highly Confidential (MNPI / client-confidential).** Vendor market data and holdings can be
  material and non-public and are entitlement-restricted; minimize any holdings/counterparty
  detail to what evidences a break, and honor each feed's license and redistribution terms.
- Retain the reconciliation, breaks, lineage, routing, and `config_version` per records policy;
  log the read and any external-delivery approval.

## Reproducibility

`reconciliation_id` + `input_fingerprint` bind the output to the exact inputs and config version;
re-running the same inputs reproduces the same breaks, routing, and tie-out.
