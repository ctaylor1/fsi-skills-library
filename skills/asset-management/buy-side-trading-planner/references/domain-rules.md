# Native input and method

Common fields: request_id, object_id, as_of and knowledge_cutoff (real dates), currency, audience=internal-review and versioned sources[]. Each used observation carries a registered source_ref. Observation sources cannot be later than the review date or known after its cutoff. Scenarios are assumptions, not observed results.

Financial values accept decimal strings (preferred for exactness); <=38 coefficient digits and exponent/adjusted exponent +/-38. Exact operations run in a private precision256 context. Ratios explicitly round to12places; portfolio PSD uses1e-30 tolerance and100-digit arithmetic. Source restrictions and missing references reject input before values are emitted.

## Required domain fields and synthetic shape

```json
{
  "maximum_adv_fraction": ".1",
  "intentions": [
    {
      "intent_id": "T1",
      "quantity": "100",
      "price": "50",
      "adv": "2000",
      "quoted_cost_bps": "8",
      "side": "buy",
      "currency": "USD",
      "market_as_of": "2026-09-21",
      "settlement_date": "2026-09-23",
      "source_ref": "S1",
      "broker_approval_status": "approved",
      "broker_approval_ref": "S1",
      "mandate_review_status": "reviewed",
      "mandate_review_ref": "S1"
    }
  ]
}
```

## Implemented algorithm

Prepare a buy-side implementation review from explicit trade intentions, current market/ADV observations, participation policy and supplied execution-cost quotes. Explain feasibility, funding and broker evidence gaps; never route or stage an order.

See the package calculator for exact field-level conventions; all fixture assumptions are synthetic and are not laws, recommended allocations or live prices. The fixture and independent-expectations file pair records independently computed numeric cases, not merely a regenerated golden.

## Unsupported scope

- Quoted cost is an estimate, not a market impact model or execution guarantee.
- No broker selection, schedule optimizer, calendar service, funding reservation or OMS connectivity.

## Evidence and boundary clarification

Each intention requires source_ref. Supplied broker_approval_ref and mandate_review_ref must resolve to eligible, approved, non-future registry entries. These references remain supplied assertions and do not authorize execution.

Actual price/market, acquisition/purchase and realized performance dates (where applicable) cannot exceed the review date, knowledge cutoff or linked source known-at date. Forward proposed trades, liability dates and other contractual assumptions remain distinct from observations.
