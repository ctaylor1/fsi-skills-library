# Controls — liquidity-stress-analyzer

- **Risk tier:** R2 — analytical. **Action mode:** Read-only analysis.
- **Human approval:** `external-delivery` — required before the pack goes outside the
  analytics team or to a case/system of record.

## Prohibited (fail closed)

- No **investment, trading, or liquidation recommendation or instruction** ("sell", "raise
  cash by", "execute the liquidation", "place the order").
- No **fund-liquidity action** or recommendation to act: gate/suspend redemptions, impose or
  raise a redemption gate, activate a side pocket, apply swing pricing, or suspend the fund.
- No **mandate/guideline/regulatory breach determination** or statement that the fund **is**
  "in breach" or "illiquid" — describe metrics factually and route breach findings to
  `mandate-compliance-monitor` plus human compliance.
- No **personalized investment, trading, or tax advice**.
- No **threshold tuning to a desired answer**; use only the versioned config.
- No **opaque scoring** presented as decisive; metrics are explainable and evidenced, and the
  scenario assumptions are always disclosed.

## Required output screens (`scripts/validate_output.py`)

- Every breached metric has ≥1 cited evidence row and a named basis.
- `suggested_band` equals the deterministic mapping from the breached-metric set.
- `scenario_assumptions` are recorded (adv_haircut, spread_multiple, price_shock,
  redemption_pct, redemption_notice_days) — transparent scenarios are mandatory.
- No recommendation/action/breach-determination language (regex screen: "suspend
  redemptions", "gate the fund", "activate side pocket", "liquidate the portfolio", "we/you
  should sell", "the fund is in breach/illiquid", "guaranteed liquidity", etc.).
- Standing disclaimer present: "Liquidity analysis and evidence only under stated scenario
  assumptions; not an investment, trading, or fund-liquidity-action determination. No trade,
  redemption gate, or other liquidity action has been taken."
- Modeling caveats included when any metric breached.

## Model risk / conduct

- The participation-of-ADV model, cost model, and thresholds are **documented and versioned**;
  they are estimates under assumptions, not forecasts. Disclose limitations (caveats).
- Do not present a single scenario as a verdict; encourage scenario variation.
- Describe patterns factually; avoid alarmist or advisory framing about the fund.

## Data classification, privacy, records

- **Highly Confidential (MNPI / client-confidential).** Minimize position data in output to
  what evidences a breached metric.
- Retain analysis + citations + `config_version` + scenario per records policy; log read +
  approval.

## Reproducibility

`analysis_id` binds output to the exact inputs, scenario assumptions, and **config version**;
re-running with the same inputs, scenario, and config reproduces the metrics and band.
