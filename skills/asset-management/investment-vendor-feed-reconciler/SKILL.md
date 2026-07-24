---
name: investment-vendor-feed-reconciler
description: >-
  Reconcile a firm's internal book-of-record against one vendor market-data feed field by field
  across five domains - prices, ratings, index constituents, corporate-action terms, and
  instrument attributes - matching on (instrument, domain, field), classifying every disagreement
  into a fixed taxonomy (value_mismatch, missing_in_internal, missing_in_vendor, stale_as_of), and
  emitting field-level discrepancies with per-source as-of times and lineage. Use when a
  market-data operations analyst asks to "reconcile internal prices/ratings/constituents/
  corporate-actions against the vendor feed", "find where our security master disagrees with the
  vendor", or "show the field-level vendor-feed breaks with as-of times". HARD BOUNDARY: this
  skill NEVER chooses the canonical value, overrides a source, or repairs a record - it surfaces
  and routes disagreements only. Price exceptions route to valuation-exception-packet; it never
  adjudicates which source is correct.
license: MIT
compatibility: Amazon Quick Desktop; requires internal-book-of-record (IBOR/security master), vendor market-data feed, reference-data/pricing-hierarchy config, and approved-calculation MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Asset Management"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Reconcile & validate"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 5 - 2026 industry expansion"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (MNPI / client-confidential)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Asset Management investment & product"
  aws-fsi-primary-user: "Market-data operations analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Investment Vendor Feed Reconciler

## Purpose and outcome
Given a firm's **internal book-of-record** observations and one **vendor market-data feed** for a
cutoff, deterministically **match** the two field by field, **classify** every disagreement into a
fixed break taxonomy with **lineage and per-source as-of times**, confirm the classified breaks
**account for every cell** (completeness tie-out), and **route** each break to its owner. A
successful output lets a market-data operations analyst see exactly which instruments and fields
disagree with the vendor, hand each discrepancy to the right owner (price exceptions to the
valuation-exception process), and give a reviewer an idempotent, cited pack to act on - **without
this skill ever choosing which value is right**.

## Use when
- "Reconcile our internal prices and ratings against the VENDOR-A feed for today."
- "Where does our security master disagree with the vendor on constituents, corporate actions, or
  instrument attributes?"
- "Show the field-level vendor-feed breaks with as-of times and route them."
- A market-data operations workflow needs a consistent, cited, reproducible internal-vs-vendor
  reconciliation.

## Do not use
- You want the skill to **choose the canonical/golden value** or decide which source is right ->
  out of scope (HARD BOUNDARY). Surface and route only; a human decides under data governance.
- You want a **price disagreement worked to a decision** -> route to `valuation-exception-packet`.
- The disagreement is a **rating or instrument-attribute** field needing a reference-data
  enrichment proposal -> `security-master-enricher`.
- The disagreement is a **corporate-action term** needing interpretation of the authoritative
  notice -> `corporate-action-interpreter`.
- You are reconciling **positions / cash vs custodian / prime broker / administrator** ->
  `position-cash-reconciliation-assistant`.
- You are performing a **NAV tie-out** across books, custodian, and administrator ->
  `nav-preparation-tie-out`.
- You are screening a **single feed** for stale/duplicate/implausible data (not a cross-source
  disagreement) -> `investment-data-quality-exception-detector` (the upstream detector).

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a discrepancy pack with a
durable `reconciliation_id`, classified breaks, per-source values/as-of times, lineage, and
per-break routing, then stops. `investment-data-quality-exception-detector` may route genuine
cross-source conflicts into it; downstream owners consume the `reconciliation_id` rather than
recomputing the comparison. It never chooses the canonical value and never repairs a record.

## Inputs and prerequisites
- `entity`, `as_of` (cutoff), `config_version`, `internal_source`, `vendor_source`, `currency`.
- **Internal observations** and **vendor observations**, each row with `instrument_id`, `domain`
  (`price` | `rating` | `index_constituent` | `corporate_action` | `instrument_attribute`),
  `field`, `value`, `as_of`, `source_ref` (and optional `currency`, `data_type`). Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Read access to the internal book and the vendor feed; approved reconciliation `config`
  (tolerances, materiality, staleness, routing) - see
  [references/domain-rules.md](references/domain-rules.md).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The internal book and the vendor feed
are **two independent observations of the same field**; a break is a disagreement between them.
The documented source hierarchy is used **only** to label lineage and route an exception to its
owner - it does **not** authorize this skill to select or write a canonical value. Cite every
break to its internal and/or vendor source rows with as-of times.

## Workflow
1. **Scope & validate** - confirm `entity`/`as_of`/`vendor_source`; load both sides for the
   cutoff; run [scripts/validate_input.py](scripts/validate_input.py). Fail closed on structural
   gaps (missing fields, unknown domain, duplicate cell on one side).
2. **Match & classify (deterministic)** - run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to index by
   `(instrument_id, domain, field)`, compare each cell (numeric tolerance or categorical exact),
   apply the staleness threshold, and classify each disagreement into the break taxonomy
   (`value_mismatch`, `missing_in_internal`, `missing_in_vendor`, `stale_as_of`). Each break
   carries `material`, lineage, per-source as-of times, `disposition: "UNRESOLVED"`, and
   `canonical_value: null`.
3. **Tie out (completeness)** - confirm `matched_cells + break_cells == total_cells` and
   `residual_cells == 0`; no cell dropped or double-counted. If it does not complete, surface the
   gap; never suppress a break.
4. **Route (evidence only)** - set each break's `route` by domain: price -> `valuation-exception-packet`,
   rating/instrument-attribute -> `security-master-enricher`, corporate-action ->
   `corporate-action-interpreter`, index-constituent -> the benchmark data owner. Routing forwards
   evidence; it does not resolve the disagreement.
5. **Write the pack** - plain-language summary + completeness tie-out + classified breaks with
   lineage/as-of + routing + the standing no-adjudication disclaimer.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py) after.
The output check confirms the completeness tie-out, the break taxonomy, lineage with as-of times,
idempotency of the `reconciliation_id`, the no-adjudication / never-repaired screen
(`canonical_value == null`, non-binding disposition, price breaks routed, no chosen-value /
override / repair / advice language), and the disclaimer. Fail closed on any miss.

## Human approval
`external-delivery`: human review required before the discrepancy pack is delivered externally or
written to a system of record. **Choosing the canonical value and writing any record are always
separate, authorized human/system actions** under data-governance segregation of duties - never
performed by this skill.

## Failure handling
- **Duplicate cell on one side** -> ambiguous pairing; fail closed and flag the data-quality gap
  rather than guessing which observation to compare.
- **Unknown `domain` or missing required field** -> fail closed; do not reconcile a malformed row.
- **Tie-out does not complete** (`residual_cells != 0`) -> surface the gap and the affected cells;
  never drop or net a cell to force agreement.
- **Ambiguous instrument identity or wrong cutoff** -> stop and confirm; never compare the wrong
  instrument or period.
- **A source is stale** -> raise `stale_as_of`; do not silently prefer the fresher side.
- **Tool timeout** -> return the cells reconciled so far with a clear "incomplete" flag; no assumed
  retry.

## Output contract
1. **Summary** - `entity`, `as_of`, `internal_source`, `vendor_source`, cell counts, break counts
   by type and domain, material-break count, `reconciliation_id`.
2. **Tie-out** - `total_cells`, `matched_cells`, `break_cells`, `residual_cells` (must be 0),
   `ties_out`, `status`.
3. **Breaks** - per break: `type`, `instrument_id`, `domain`, `field`, per-source `value`/`as_of`,
   numeric `difference` or `as_of_gap_days`, `material`, lineage citations, `route`,
   `disposition: "UNRESOLVED"`, `canonical_value: null`.
4. **Routing** - breaks grouped by owner; every price-domain break under `valuation-exception-packet`.
5. **Machine-readable** - the full reconciliation JSON + `reconciliation_id` + `input_fingerprint`
   for downstream owners and reproducibility.
6. **Standing disclaimer** - "Field-level discrepancy report only; this skill does not choose the
   canonical value, override a source, or repair any record. Price exceptions are routed to the
   valuation-exception process. All discrepancies require human review before any system-of-record
   change."
See [references/controls.md](references/controls.md).

## Privacy and records
Highly Confidential (MNPI / client-confidential). Vendor data and holdings can be material,
non-public, and entitlement-restricted; minimize any holdings/counterparty detail to what
evidences a break and honor each feed's license and redistribution terms. Retain the
reconciliation, breaks, lineage, routing, and `config_version` per records policy; log the read
and any external-delivery approval.

## Gotchas
- **Surface, never select.** The skill has no canonical-selection operation. `canonical_value:
  null`, `disposition: "UNRESOLVED"`, and routing are load-bearing controls, not decoration -
  choosing a value would breach the HARD BOUNDARY.
- **Prices route, they don't resolve.** Every price break (including a stale price whose values
  agree) goes to `valuation-exception-packet`; the reconciler never argues a mark.
- **Staleness is a break even when values agree.** A source older than the threshold is surfaced
  as `stale_as_of`; agreeing on a stale number is not a clean match.
- **Completeness, not a balance.** The tie-out is a cell partition (matched + breaks == total),
  not an amount residual - a dropped or double-counted cell is the failure.
- **Config is a versioned contract.** Tolerances, materiality, staleness, and routing come from
  `config`, never tuned per-run to make a break disappear.
- **One vendor per run.** Compare additional vendors as separate pairwise runs; do not blend feeds
  into a single "consensus" value (that would be choosing a canonical value).
