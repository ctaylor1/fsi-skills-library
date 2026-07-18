# Controls — dcf-modeler

- **Risk tier:** R2 — analytical / drafting support. **Action mode:** Draft-only; no
  system-of-record change.
- **Human approval:** `external-delivery` — required before the model is delivered to a
  client, deal team, data room, or CRM, or otherwise written to a system of record.

## Prohibited (fail closed)

- No **investment recommendation** (buy / sell / hold / accumulate / reduce / over- or
  under-weight) and no implication of one.
- No **price target**, **fair-value verdict presented as a decision**, or **fairness
  opinion** — these are licensed-human / investment-committee outputs.
- No **guarantee** of return, upside, or future price.
- No **personalized investment, legal, or tax advice**.
- No **assumption without provenance**; no formula, tolerance, or scenario delta bent to
  reach a target valuation.
- No **Gordon terminal value when `WACC <= g`** (invalid; fail closed).

## Required output screens (`scripts/validate_output.py`)

- Every scenario ties out: `sum(PV of UFCF) + PV(TV) == enterprise_value`; each year's
  `PV == UFCF * discount_factor`; discount factors non-increasing; bridge and per-share
  tie-outs hold.
- `base`, `upside`, `downside` present and monotonic on enterprise, equity, and per-share
  value (`downside <= base <= upside`).
- Gordon guard: `WACC > terminal growth`.
- Every `assumptions_register` entry has a non-empty `provenance` **and** `citation`.
- `model_id` and `inputs_hash` present (reproducibility).
- No investment-advice / recommendation / price-target / fairness-opinion language in the
  author narrative (regex screen).
- Standing disclaimer present: "Illustrative valuation model for analytical purposes only;
  not investment advice, not a recommendation to buy, sell, or hold any security, not a
  price target, and not a fairness opinion. Outputs depend entirely on the stated
  assumptions, which a qualified human must review."

## Data classification, privacy, records

- **Highly Confidential (MNPI / client-confidential).** A DCF often embeds material
  non-public information (management guidance, deal assumptions). Treat the model, its
  inputs, and its `model_id` as need-to-know.
- Respect information barriers / wall-crossing; do not move MNPI across a public-side / wall.
- Retain the model, its assumptions register, and `config_version` per records policy; log
  the read and any external-delivery approval.

## Reproducibility & change control

`inputs_hash` binds the model to the exact numeric assumptions; the `config_version` binds
the scenario deltas, tolerance, and discount convention. Re-running the same inputs and
config reproduces the same `model_id` and the same numbers. Changing an assumption changes
the hash — the audit trail shows what moved.

## Separation of duties

Building the model (this skill) is separate from independently reviewing it and from
approving external delivery. The model is a draft input to a human's judgment, never a
substitute for it.
