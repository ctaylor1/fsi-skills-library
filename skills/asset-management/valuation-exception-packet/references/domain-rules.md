# Domain Rules — valuation-exception-packet

Orientation references: the firm's **valuation policy** and pricing-committee charter, fair-value
measurement principles (observable vs unobservable inputs / price-input hierarchy), and the
approved **valuation-tolerance config**. The firm's policy and its versioned tolerance config
take precedence and are **versioned contracts**.

## Pricing hierarchy (observed → hypothesis)

Candidate prices are ranked by this hierarchy. Rank informs which price sits highest **for
reference**; it does **not** select the price (the committee does).

| Rank | Source type | Class |
| ---- | ----------- | ----- |
| 1 | `exchange_close` — official close in an active market (Level 1) | observation |
| 2 | `vendor_evaluated` — approved-vendor evaluated price | observation |
| 3 | `executable_quote` — firm/executable broker quote | observation |
| 4 | `trade_print` — arm's-length executed trade, sufficient size | observation |
| 5 | `indicative_quote` — non-firm broker indication | hypothesis |
| 6 | `matrix_price` — matrix/spread-based estimate | hypothesis |
| 7 | `model_price` — model/comparable estimate (unobservable inputs, Level 3) | hypothesis |
| 8 | `carry_forward` — prior-day price carried forward | hypothesis (stale) |

**Rule:** a price whose `source_type` is a hypothesis is tagged `price_type: hypothesis` and is
never counted as an observed price. An instrument with **no observed price** is a `missing`
exception even when hypotheses are available.

## Exception taxonomy (deterministic thresholds)

Thresholds are **configuration by asset class**, defaulted below and overridable via
`asset_class_tolerances` in the input. All comparisons use the versioned config.

| Exception | Deterministic condition |
| --------- | ----------------------- |
| `stale` | Observed prices exist, but business days from the latest observed as-of to `as_of` > `staleness_max_days[asset_class]`. |
| `missing` | No observed price for `as_of` from any approved source (hypotheses do not satisfy this). |
| `disputed` | An `open_challenge` is flagged, **or** cross-source dispersion of observed prices > `dispute_tolerance_pct[asset_class]`. |
| `outlier` | A `prior_price` and a same-day observed price exist and \|day-over-day move\| > `outlier_move_pct[asset_class]`. |

An instrument may carry more than one exception type. `open_challenge` also forces the top
severity band (P1). Corporate-action context (splits/dividends) is cited to explain—not to
suppress—a move; suppression is never automatic.

### Default tolerances (config `valuation-tolerances@v2026.07`)

| Asset class | `staleness_max_days` | `outlier_move_pct` | `dispute_tolerance_pct` |
| ----------- | -------------------- | ------------------ | ----------------------- |
| `equity` | 1 | 10 | 1.0 |
| `corporate_bond` | 2 | 5 | 1.0 |
| `government_bond` | 1 | 3 | 0.5 |
| `private_placement` | 5 | 15 | 3.0 |
| _default (unknown class)_ | 2 | 10 | 2.0 |

## Severity scoring (deterministic, documented)

Severity is a triage rank for the committee queue, computed from explainable inputs — **not** a
valuation conclusion.

| Input | Contribution (default) |
| ----- | ---------------------- |
| Exception type (max over types) | `missing` +4, `disputed` +3, `outlier` +3, `stale` +2 |
| Outlier magnitude | move ≥ 25% +3, else ≥ 10% +2 |
| Dispersion magnitude | ≥ 5% +3, else ≥ 1% +1 |
| Materiality (\|market_value\|) | ≥ 1,000,000 +3, else ≥ 100,000 +1 |
| Illiquid asset class (`corporate_bond`/`government_bond`/`private_placement`) | +2 |
| Open challenge | +2 |

Bands: **P1 (Elevated)** total ≥ 7 **or** any open challenge; **P2 (Standard)** 3–6;
**P3 (Low)** ≤ 2. `validate_output` recomputes the band from the score (+ open-challenge
override) and rejects any mismatch.

## Durable case & job IDs

- Per-instrument case: `VEP-{as_of:YYYYMMDD}-{instrument_id}` (stable, reproducible).
- Packet job: `VEP-JOB-{as_of:YYYYMMDD}-{book}`.

These IDs are the handoff anchors to the valuation committee and to `nav-preparation-tie-out`;
they are deterministic so re-running the same book/date yields the same IDs.

## Hard boundaries (fail closed)

- No **price selection / override** and no statement of the "correct" price.
- No **NAV certification or striking**, and no accounting-entry posting.
- No **hypothesis presented as an observed price**.
- No **closure/resolution/finalization** of an exception; disposition is recommendation-only.
- No **auto-suppression** of a move on corporate-action grounds; context is cited, the exception
  still routes to the committee.

## Evidence bundle — required contents

Durable `case_id`; the `exception_type`(s); a chronology of priced observations and hypotheses
with as-of times; parties (masked) with roles (vendor/broker/exchange/challenger); amounts
(observed prices vs hypotheses, and market value where provided); the pricing-hierarchy
reference; metrics (staleness business days, day-over-day move %, cross-source dispersion %);
a citation for every item; `recommended_next_step` (advisory); `adjudication: human-required`.
