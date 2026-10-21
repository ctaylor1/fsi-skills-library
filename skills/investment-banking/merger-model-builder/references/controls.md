# Controls — merger-model-builder

- **Risk tier:** R2 — analytical / drafting. **Action mode:** Draft-only; no system-of-record change.
- **Human approval:** `external-delivery` — required before the model is delivered to a
  client, committee, or system of record.

## Prohibited (fail closed)

- No **investment advice, buy/sell/hold view, price target, or recommendation to transact**
  ("we recommend acquiring", "should proceed", "attractive acquisition", "strong buy").
- No **valuation or fairness opinion** ("what it's worth", "the price is fair", "fair from a
  financial point of view") — that is a licensed human specialist's role.
- No **system-of-record write** or transaction authorization; the model is a draft artifact.
- No **driver tuning to force a verdict**; drivers come from sourced, versioned terms and are
  labelled as estimates where they are estimates.
- No **opaque or unreproducible model**; every figure ties out from stated components.

## Required output screens (`scripts/validate_output.py`)

- **Formula tie-outs** recompute independently: cash + stock = offer value; new shares =
  stock consideration / acquirer price; pro forma shares = acquirer shares + new shares; pro
  forma EPS = pro forma NI / pro forma shares; accretion $/% recompute; ownership recomputes
  and sums to 100%; verdict matches the sign of accretion.
- **Assumption provenance**: non-empty assumptions list; every driver carries a citation; the
  required drivers (mix, premium, synergies, tax, debt rate) are present.
- **Scenario behavior**: base/upside/downside present and accretion monotonic (upside >= base
  >= downside within tolerance).
- **Reproducibility**: `model_id` present and stamped with `assumptions_version`; the
  self-asserted `tie_outs` block is confirmed by the independent recompute.
- **No advice language** and the standing disclaimer present: "Illustrative pro forma model
  based on stated assumptions; not investment advice, a fairness opinion, or a recommendation
  to transact."

## Model risk / conduct

- Label management estimates (synergies, write-ups) as estimates; carry uncertainty in the
  scenario range rather than a single point.
- Tax-effect adjustments consistently; intangible amortization is tax-effected only when
  deductible.
- Transaction fees are one-time and excluded from run-rate EPS; do not double-count.

## Data classification, privacy, records

- **Highly Confidential (MNPI / client-confidential).** Use deal code names; minimize
  identifying data in the output.
- Retain the model, inputs, and `assumptions_version` for reproducibility; log the read and
  any external-delivery approval.

## Reproducibility

`model_id` binds the output to the deal, as-of date, and **assumptions version**; re-running
with the same inputs and version reproduces every figure, scenario, and sensitivity cell.
