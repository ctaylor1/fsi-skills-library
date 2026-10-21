# Controls — lbo-model-builder

- **Risk tier:** R2 — analytical / drafting support. **Action mode:** Draft-only; no
  system-of-record change.
- **Human approval:** `external-delivery` — required before the model is delivered to a
  client, deal team, investment committee, data room, or CRM, or otherwise written to a
  system of record.

## Prohibited (fail closed)

- No **investment recommendation** (invest / pass / commit / allocate / proceed / walk away)
  and no implication of one.
- No **guarantee** of a return, IRR, MOIC, or multiple, and no presentation of a modelled
  return as a promised outcome.
- No **investment-committee approval**, **fund-allocation decision**, or **fairness opinion**
  — these are licensed-human / investment-committee outputs.
- No **personalized investment, legal, or tax advice**.
- No **assumption without provenance**; no formula, tolerance, fee, leverage, or scenario
  delta bent to reach a target return.
- No **unbalanced Sources & Uses** (`total_sources != total_uses`) and no debt schedule that
  does not roll forward — these are formula failures, not modelling choices.

## Required output screens (`scripts/validate_output.py`)

- **Sources & Uses balance:** `total_sources == total_uses`; `sponsor_equity == total_uses -
  total_new_debt`; `total_new_debt == sum(tranche principals)`; purchase EV `== entry_ebitda
  * entry_multiple`.
- **Debt & cash roll-forwards (per scenario, per year):** interest `== sum(rate * beginning
  balance)`; `fcf_before_sweep == EBITDA - interest - cash taxes - capex - dNWC - mandatory
  amort`; each tranche `ending == beginning - mandatory - sweep`; cash `ending == beginning +
  fcf_before_sweep - optional sweep`; year-1 tranche beginning `==` its S&U principal.
- **Exit & returns:** exit EV `== exit EBITDA * exit multiple`; exit equity `== exit EV - net
  debt`; MOIC `== exit equity / sponsor equity`; `(1 + IRR)^hold == MOIC`.
- **Scenario behaviour:** `base`, `upside`, `downside` present and monotonic on exit equity,
  MOIC, and IRR (`downside <= base <= upside`).
- Every `assumptions_register` entry has a non-empty `provenance` **and** `citation`.
- `model_id` and `inputs_hash` present (reproducibility).
- No investment-advice / recommendation / return-guarantee / IC-approval language in the
  author narrative (regex screen).
- Standing disclaimer present: "Illustrative leveraged-buyout model for analytical purposes
  only; not investment advice, not a recommendation to make, hold, or exit any investment,
  not a guarantee of any return, IRR, or multiple, and not an investment-committee approval.
  Outputs depend entirely on the stated assumptions, which a qualified human must review."

## Data classification, privacy, records

- **Highly Confidential (MNPI / client-confidential).** An LBO model embeds material
  non-public information (management projections, deal price, financing terms). Treat the
  model, its inputs, and its `model_id` as need-to-know.
- Respect information barriers / wall-crossing; do not move MNPI across a public-side / wall.
- Retain the model, its assumptions register, and `config_version` per records policy; log
  the read and any external-delivery approval.

## Reproducibility & change control

`inputs_hash` binds the model to the exact numeric assumptions; the `config_version` binds
the scenario deltas, tolerance, and fee/leverage defaults. Re-running the same inputs and
config reproduces the same `model_id` and the same numbers. Changing an assumption changes
the hash — the audit trail shows what moved.

## Separation of duties

Building the model (this skill) is separate from independently reviewing it and from
approving external delivery or any investment decision. The model is a draft input to a
human's judgment, never a substitute for it.
