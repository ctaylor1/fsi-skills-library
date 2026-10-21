# Domain Rules - kpi-segment-bridge-builder

## Version 0.2.0 contract

Use only closed historical periods with permitted sourced inputs. Referenced authoritative totals must exist. Unrequested reconciliation is not evaluated and never counts as reconciled; the pack reports partial-or-not-evaluable coverage. Mapping IDs are unique, approved and effective on/before the prior-period end so both bridged periods are covered. Full supplied context, including totals/citations/mappings, affects hashes. The volume-price joint term is a two-factor interaction, not general product-mix attribution.


The deterministic bridge math, the source-type and mapping discipline, and the tie-outs.
Conventions, tolerances, and the approved mapping set are **configuration** (versioned, owned by
research / model-governance and accounting policy), not the skill's judgment, and are never bent
to reach a desired decomposition. Orientation: standard KPI / price-volume / segment bridging as
used in equity research and banking; the firm's disclosure standard takes precedence where it
differs.

## What this skill does - and the two hard boundaries

It **extracts disclosed operational KPIs** and **constructs revenue / margin / volume-price /
segment bridges** between two **closed, reported** periods, tying every component to a disclosure
and reconciling to the reported totals. It is a *historical decomposition*.

- **HARD BOUNDARY 1 - never forecast.** No future period, no projection, no extrapolation. Every
  input must be historical/disclosed; a forward-looking `source_type` is rejected on input and
  output. Forward work routes to the forecasting skills (see `references/handoffs.md`).
- **HARD BOUNDARY 2 - never normalize accounting judgment beyond approved mappings.** Any
  reclassification/re-mapping must use an approved, effective `mapping_id`. Discretionary
  normalization routes to `financials-normalizer` / accounting policy.

## Bridge families (in `scripts/calculate_or_transform.py`)

### `walk` - additive walk of disclosed signed components

```
total_change      = ending - beginning
walk ties out iff:  beginning + sum(component amounts) == ending   (within tolerance)
contribution_i    = amount_i / total_change        (when total_change != 0)
```

Used for disclosed revenue walks (volume / price / FX / M&A-scope / mix), disclosed margin-point
walks, and **segment** bridges (each component is a segment's contribution to the total change).
Components are **disclosed**, not invented by the skill; a re-mapped component (e.g. FX via a
constant-currency mapping, or an inorganic carve-out) must reference an approved `mapping_id`.

### `volume_price` - two-factor decomposition from disclosed units and price

A deterministic decomposition of a revenue delta using **base-period weighting with an explicit
joint (mix) cross-term** (`config` convention `base_period_weighted_with_joint_mix`):

```
beginning = units_0 * price_0
ending    = units_t * price_t
volume    = (units_t - units_0) * price_0
price     = (price_t - price_0) * units_0
mix       = (units_t - units_0) * (price_t - price_0)     # joint / cross term
volume + price + mix == ending - beginning               # exact by construction
```

Units and price are **disclosed** (KPI supplement); the three effects are `derived` (computed
from disclosed factors), not forecast. The convention is fixed configuration and is stated in the
pack so the split is reproducible and defensible; the skill does not choose a weighting to
flatter a component.

## Reconciliation to authoritative (disclosed) totals

Where a bridge names a `reconcile_to` key, its `beginning`/`ending` must equal the corresponding
`reported_totals` entry (the stated authoritative/disclosed figure) within tolerance. A bridge
that decomposes a change but does not reconcile to the disclosed total is a control failure.

## Tie-outs (every one must hold within tolerance; re-derived in validate_output)

1. `walk`: `beginning + sum(components) == ending`.
2. `volume_price`: `volume`, `price`, `mix` re-derived from factors match, and sum to the delta;
   `beginning == units_0*price_0`, `ending == units_t*price_t`.
3. contribution shares sum to ~1 when the total change is non-zero.
4. each bridge reconciles to its stated disclosed total (`reconcile_to`).
5. no forward-looking `source_type` anywhere; every `mapping` component references an approved
   mapping.

## Source-type discipline

Admissible (historical/disclosed): `reported`, `disclosed`, `actual`, `filing`, `audited`,
`derived`. Rejected (forward-looking): `forecast`, `projection`, `guidance`, `estimate`,
`consensus`, `target`, `budget`, `plan`, `model-output`. Enforced in both scripts.

## Mapping discipline & effective dates

The approved mapping registry is a versioned contract (`mapping_version`). A mapping is usable
only if `status == approved` and its `effective_date` is on or before the reporting period. Any
`mapping`-derived component whose `mapping_id` is missing, unapproved, or not-yet-effective is
rejected. New reclassifications must be approved via `financials-normalizer` / accounting policy
before they can appear here.

## Versioning, durable IDs & reproducibility

- `config_version` binds the decomposition convention, tolerance, and allowed source types.
- `mapping_version` binds the approved mappings.
- `job_id` is the durable job identifier for the extraction/build; the caller may supply it,
  otherwise it is derived deterministically.
- `pack_id = kpi-bridge-{company}-{current_period}-{inputs_hash}`, where `inputs_hash` is a hash
  of the disclosed inputs and mapping set. Identical inputs and versions reproduce the identical
  pack and numbers.

## Hard boundaries (fail closed)

- Never output or imply a **forecast/projection** of any KPI, segment, margin, volume, or price.
- Never apply a **normalization/reclassification** that is not an approved, effective mapping.
- Never present an **untied bridge** or one that fails to reconcile to the disclosed total.
- Never output an **investment recommendation**, **price target**, **fair-value verdict**, or
  **guarantee**; never give personalized investment/legal/tax advice.
- Never fabricate or leave **unsourced** a component; every number carries provenance + citation.
