# Controls - kpi-segment-bridge-builder

- **Risk tier:** R2 - analytical / drafting support. **Action mode:** Draft-only; no
  system-of-record change.
- **Human approval:** `external-delivery` - required before the bridge pack is delivered to a
  client, deal team, data room, CRM, or written to a model of record.

## Prohibited (fail closed)

- **No forecast.** The skill decomposes disclosed, historical/actual results only. It never
  projects, forecasts, or extrapolates a future KPI, segment, margin, volume, or price, and no
  bridge input may carry a forward-looking `source_type` (forecast / projection / guidance /
  estimate / consensus / target / budget / plan / model-output).
- **No accounting normalization beyond approved mappings.** Reclassifications, segment recasts,
  constant-currency, and inorganic carve-outs are permitted **only** through an approved,
  effective `mapping_id`. No discretionary/ad-hoc normalization, non-GAAP adjustment, or
  restatement judgment.
- **No investment recommendation** (buy / sell / hold / over- or under-weight), **price
  target**, **fair-value verdict**, or **guarantee** - licensed-human / committee outputs.
- No **personalized investment, legal, or tax advice**.
- **No untied bridge.** A bridge whose components do not reconcile to its ending value, or a
  bridge that does not reconcile to the stated disclosed total, is never presented as valid.
- No **assumption without provenance**; no convention, tolerance, or mapping bent to reach a
  wanted decomposition.

## Required output screens (`scripts/validate_output.py`)

- Every `walk` bridge ties out: `beginning + sum(components) == ending`; contribution shares
  sum to ~1 when the total change is non-zero.
- Every `volume_price` bridge re-derives from disclosed factors: `volume = (u_t-u_0)*p_0`,
  `price = (p_t-p_0)*u_0`, `mix = (u_t-u_0)*(p_t-p_0)`; the three sum to the revenue delta and
  `beginning=u_0*p_0`, `ending=u_t*p_t`.
- Reconciliation to disclosed totals holds wherever a bridge names a `reconcile_to` key.
- No forward-looking `source_type` on any component or register entry (never forecast).
- Every `mapping`-derived component references a `mapping_id` that is present AND `approved` in
  the `mapping_register`; no unapproved mapping (never normalize beyond approved mappings).
- Every `assumptions_register` entry has non-empty `provenance` AND `citation`;
  `config_version` and `mapping_version` present.
- `pack_id` and `inputs_hash` present (reproducibility).
- No forecast/projection or investment-advice/recommendation/price-target language in the
  author narrative (regex screen).
- Standing disclaimer present: "Historical, source-linked KPI/segment bridge for analytical
  purposes only; a decomposition of disclosed, reported results. It is not a forecast, not
  normalized accounting, not investment advice, and not a recommendation. Every figure ties to
  a disclosed source, and a qualified human must review it before any use."

## Data classification, privacy, records

- **Highly Confidential (MNPI / client-confidential).** KPI extraction and bridges can embed
  material non-public information (pre-release results, deal context). Treat the pack, its
  inputs, `pack_id`, and `job_id` as need-to-know.
- Respect information barriers / wall-crossing; do not move MNPI across a public-side wall.
- Retain the pack, its assumptions register, mapping register, `config_version`, and
  `mapping_version` per records policy; log the read and any external-delivery approval.

## Reproducibility & change control

`inputs_hash` binds the pack to the exact disclosed inputs and mapping set; `config_version`
binds the decomposition convention and tolerance; `mapping_version` binds the approved mappings.
Re-running the same inputs and versions reproduces the same `pack_id` and the same numbers.
Changing an input or a mapping changes the hash - the audit trail shows what moved.

## Separation of duties

Building the bridge (this skill) is separate from forecasting it forward, from normalizing the
underlying statements, from independently reviewing it, and from approving external delivery.
The bridge is a draft, source-tied input to a human's judgment, never a substitute for it.
