# Native input and method

Common fields: request_id, object_id, as_of and knowledge_cutoff (real dates), currency, audience=internal-review and versioned sources[]. Each used observation carries a registered source_ref. Observation sources cannot be later than the review date or known after its cutoff. Scenarios are assumptions, not observed results.

Financial values accept decimal strings (preferred for exactness); <=38 coefficient digits and exponent/adjusted exponent +/-38. Exact operations run in a private precision256 context. Ratios explicitly round to12places; portfolio PSD uses1e-30 tolerance and100-digit arithmetic. Source restrictions and missing references reject input before values are emitted.

## Required domain fields and synthetic shape

```json
{
  "nav": "1000",
  "nav_tolerance": "0",
  "settled_cash": "100",
  "cash_buffer": "40",
  "target_cash_weight": ".05",
  "settlement_date": "2026-09-23",
  "holdings": [
    {
      "id": "EQ",
      "quantity": "9",
      "price": "100",
      "price_as_of": "2026-09-21",
      "lot_size": "1",
      "target_weight": ".95",
      "fee_bps": "10",
      "source_ref": "S1"
    }
  ]
}
```

## Implemented algorithm

Build a lot-rounded draft rebalance from supplied targets, current quantities, prices, cash and costs. Reconcile NAV and funding; never choose targets, submit orders or assume unsettled proceeds are available.

See the package calculator for exact field-level conventions; all fixture assumptions are synthetic and are not laws, recommended allocations or live prices. The fixture and independent-expectations file pair records independently computed numeric cases, not merely a regenerated golden.

## Unsupported scope

- Single-currency long-only supplied targets; fractional existing units preserved, target lots floor-rounded.
- Single explicit settlement date; no calendar service, tax optimizer, order generation or fill assumptions.

## Evidence and boundary clarification

Each holdings row requires a source_ref for its supplied position/price/lot inputs. NAV, cash, tolerance and target weights are explicitly supplied review assumptions and must be independently reconciled before action.

Actual price/market, acquisition/purchase and realized performance dates (where applicable) cannot exceed the review date, knowledge cutoff or linked source known-at date. Forward proposed trades, liability dates and other contractual assumptions remain distinct from observations.
