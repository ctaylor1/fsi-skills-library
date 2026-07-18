# Controls — three-statement-model-builder

- **Risk tier:** R2 — analytical / drafting support. **Action mode:** Draft-only; no
  system-of-record change.
- **Human approval:** `external-delivery` — required before the model is delivered to a
  client, deal team, data room, or CRM, or otherwise written to a system of record.

## Prohibited (fail closed)

- No **investment recommendation** (buy / sell / hold / accumulate / reduce / over- or
  under-weight) and no implication of one.
- No **price target**, **fair-value verdict presented as a decision**, or **fairness
  opinion** — these are licensed-human / investment-committee outputs.
- No **valuation conclusion**: this skill builds the *operating model* (the three linked
  statements); discounting it to a value is `dcf-modeler`'s job, and the value judgment is a
  human's.
- No **guarantee** of return, upside, or future results; the model is *not a forecast of
  actual results*.
- No **personalized investment, legal, accounting, audit, or tax advice**.
- No **assumption without a source**; no formula, tolerance, or scenario delta bent to reach
  a wanted output.
- No **hiding a base-year imbalance**: a historical balance sheet that does not tie is
  surfaced, never silently plugged.

## Required output screens (`scripts/validate_output.py`)

Each check is **re-derived independently** from the stored statements (the model's own
`checks` block is not trusted):

- **Balance-sheet identity** every year: `total_assets == total_liabilities + equity`.
- **Cash tie** every year: cash-flow `ending_cash == balance_sheet cash`.
- **Equity roll-forward**: `equity_t == equity_{t-1} + net_income_t - dividends_t`.
- **PP&E roll-forward**: `ppe_t == ppe_{t-1} + capex_t - depreciation_t`.
- **Assumption provenance**: every driver assumption carries a non-empty `source`, and the
  full required-driver set is covered.
- **Scenario behaviour**: `base`, `upside`, `downside` present and final-year revenue
  monotone (`upside >= base >= downside`).
- **Reproducibility**: `model_id`, `config_version`, and `inputs_hash` present.
- **No investment advice**: no buy/sell/hold, rating, price-target, or recommendation
  language in the author narrative (regex screen).
- **Standing disclaimer present**: "Model output for analytical support only; not
  investment advice or a recommendation to buy, sell, or hold any security."

**Fail closed on any miss.**

## Data classification, privacy, records

- **Highly Confidential (MNPI / client-confidential).** An operating model often embeds
  material non-public information (management guidance, deal assumptions). Treat the model,
  its inputs, and its `model_id` as need-to-know.
- Respect information barriers / wall-crossing; do not move MNPI across a public-side / wall.
- Retain the model, its assumptions, and `config_version` per records policy; log the read
  and any external-delivery approval.

## Reproducibility & change control

`inputs_hash` binds the model to the exact numeric assumptions; the `config_version` binds
the scenario deltas, tolerance, and conventions. Re-running the same inputs and config
reproduces the same numbers. Changing an assumption changes the hash — the audit trail shows
what moved.

## Separation of duties

Building the model (this skill) is separate from independently reviewing it and from
approving external delivery. The model is a draft input to a human's judgment, never a
substitute for it.
