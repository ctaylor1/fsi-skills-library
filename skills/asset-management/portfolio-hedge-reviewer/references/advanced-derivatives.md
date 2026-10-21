# Advanced derivatives: supplied full-repricing challenge

Select `extension: advanced-derivatives` explicitly. The existing input without an extension keeps the original first-order method and output. Unknown extension values fail rather than falling back to the linear method. Both use the existing script entrypoints; advanced output validation requires `--input` with the detached original.

## Practitioner workflow

Scope the unchanged portfolio, human-defined candidate full books, contract versions, valuation date and currency. The accountable model owner supplies the pricing/risk engine and its accepted product/method scope. Retain payoff terms, position quantity units, calendar, market/curve/volatility snapshots, valuation adjustments and known model limitations. Describe omitted funding, collateral, counterparty and basis risks explicitly.

Obtain full-book base and stress present values and the explicitly defined sensitivities from that engine. Do not derive nonlinear option prices, Greeks, XVA or combined-book netting effects using the package's original linear method. Specify all relevant book/scenario/measure identities and exact units before receiving values. Obtain a separately sourced independent benchmark with method/version, input binding and tolerances. Matching supplied labels and hashes does not authenticate either institutional acceptance or benchmark independence.

Run the bounded review. Version, context, hash, coverage or unit contradictions fail validation. An unavailable, partial, unsupported, failed or unreconciled engine withholds dependent comparison values; no alternative pricer is selected. A complete consistent result still needs a specialist to assess calibration, assumptions, missing risks and fitness for the actual book.

Present candidate books neutrally using [the advanced output template](../assets/advanced-derivatives-template.md). No candidate ranking, sizing, recommendation, order staging or execution is authorized.

## Input schema

The advanced request uses the common `investment-foundation/1.0` fields: request_id, object_id, as_of, knowledge_cutoff, currency, audience=`internal-review`, versioned sources and optional unresolved_issues, plus extension=`advanced-derivatives`. Each actual source must be eligible for date/cutoff/audience. No `mode` key is supported.

`engine_request`, `engine_result` and `independent_benchmark` use the [specialist contract](specialist-engine-contract.md). Results and benchmark may be null, yielding an unavailable review. Each complete result repeats the full request hash, engine/model/method versions and review context. Decimal result values and tolerances must be strings or integers, never binary floats.

`engine_request.input` additionally requires:

- portfolio_id matching object_id; valuation_method=`full-repricing`; cost_basis=`excludes-transaction-cost`.
- Pinned market_data_snapshot, curve_snapshot, volatility_snapshot and calendar_version; an explicit valuation_adjustments statement and nonempty model_limitations list.
- `instruments[]`: unique instrument_id, product_type, nonempty supplied `terms` object and source_ref. Economic completeness and accepted product scope remain model-owner responsibilities.
- `books[]`: unique book_id, role=`baseline` or `hedged`, source_ref and nonempty positions list with unique known instrument_id, finite signed quantity and quantity_unit. Exactly one baseline and at least one human-defined candidate are required. Combined-book values are independently supplied by the pricing engine.
- `scenarios[]`: unique scenario_id, version, source_ref and shocks object. Scenario `base` has an empty shock object; at least one other scenario must contain explicit `{unit, value}` shocks. No scenario is generated or calibrated locally.
- `measures[]`: unique measure_id, explicit unit/definition and source_ref. The `pv` measure uses the exact review currency; sensitivities retain their supplied units without aggregation or conversion.
- `candidate_costs[]`: one row per hedged book, book_id, nonnegative amount, exact currency, source_ref, common nonempty horizon and basis=`one-time-cash-cost`. Costs already included in pricing must not be supplied again under this method.

Engine expected metric IDs are exactly `book_id|scenario_id|measure_id` for the full Cartesian inventory, with each measure's unit. IDs cannot contain the separator. Each inventory permits at most 10,000 rows; the shared engine contract limits the expanded metric inventory to 10,000. No missing metric is zero.

## Local arithmetic and interpretation

For each full book, scenario P&L equals its supplied scenario PV less its own supplied base PV. Incremental hedge-book P&L is candidate-book scenario P&L less baseline-book scenario P&L. Subtract the explicitly supplied one-time cash cost to show the cost-adjusted candidate-book P&L. These differences do not assume that standalone derivative values add linearly, and they do not convert Greeks into prices.

The independent synthetic example has baseline PV 100 → 60 and candidate PV 105 → 90. The book P&Ls are −40 and −15, incremental P&L is 25, and a supplied cost of 2 yields −17 candidate P&L after cost. These are supplied test values, not outputs of a working nonlinear pricing engine.

All differences and tolerance comparisons use exact bounded decimals. Benchmark pass means supplied consistency only. The result leaves hedge_selection null and trade_authorized false. Current institutional model validation, licensed data/engine access, source fidelity, legal treatment and professional acceptance are external gates.

## Method-governance sources

Primary references checked 2026-10-04:

- [Federal Reserve SR 26-2, Revised Guidance on Model Risk Management](https://www.federalreserve.gov/supervisionreg/srletters/SR2602.htm), dated April 17, 2026, is current supervisory background for conceptual soundness, validation, monitoring and model limitations. Its applicability depends on the institution; this package is not a supervisory compliance certification.
- [Federal Reserve model risk guidance text](https://www.federalreserve.gov/frrs/guidance/supervisory-guidance-on-model-risk-management.htm) supports keeping model limitations and effective challenge distinct from a mechanical benchmark comparison.
- [BIS Basel Framework, market risk](https://www.bis.org/committees/bcbs/basel-framework/standard/mar?allChapters=true) provides banking-specific independent pricing/model validation context. No capital method, required regulatory metric or jurisdictional adoption is inferred here.

The local PV-difference identity is elementary arithmetic, not a financial pricing methodology. All advanced prices and risks remain delegated to the supplied engine contract.
