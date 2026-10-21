# Native input and method

Common fields: request_id, object_id, as_of and knowledge_cutoff (real dates), currency, audience=internal-review and versioned sources[]. Each used observation carries a registered source_ref. Observation sources cannot be later than the review date or known after its cutoff. Scenarios are assumptions, not observed results.

Financial values accept decimal strings (preferred for exactness); <=38 coefficient digits and exponent/adjusted exponent +/-38. Exact operations run in a private precision256 context. Ratios explicitly round to12places; portfolio PSD uses1e-30 tolerance and100-digit arithmetic. Source restrictions and missing references reject input before values are emitted.

## Required domain fields and synthetic shape

```json
{
  "jurisdiction": "US",
  "account_type": "taxable-equity",
  "sale_date": "2026-09-21",
  "related_accounts_coverage": "complete",
  "selected_lots": [
    {
      "lot_id": "LOT1",
      "sale_quantity": "10",
      "available_quantity": "10",
      "basis_per_unit": "100",
      "sale_price": "80",
      "supplied_tax_rate": ".2",
      "acquired": "2025-01-01",
      "tax_identity": "ABC-reviewed",
      "source_ref": "S1"
    }
  ],
  "related_purchases": [
    {
      "purchase_id": "P1",
      "tax_identity": "ABC-reviewed",
      "trade_date": "2026-09-10",
      "quantity": "5",
      "source_ref": "S1"
    }
  ]
}
```

## Implemented algorithm

Review the estimated tax and wash-sale evidence for explicitly selected US taxable equity lots using supplied rates and substantially-identical mappings. Draft lot-impact evidence; no tax advice, automatic lot selection or realized deduction claim.

See the package calculator for exact field-level conventions; all fixture assumptions are synthetic and are not laws, recommended allocations or live prices. The fixture and independent-expectations file pair records independently computed numeric cases, not merely a regenerated golden.

## Unsupported scope

- No wash-sale basis allocation or deduction determination; mappings/rates are supplied assertions.
- No state, cross-border, derivative, IRA or retirement tax engine. All loss benefits withheld for review.

## Evidence and boundary clarification

The selected_lots scope must be nonempty. Every selected lot and related purchase requires a source_ref; a nonempty source registry alone is insufficient evidence linkage.

Actual price/market, acquisition/purchase and realized performance dates (where applicable) cannot exceed the review date, knowledge cutoff or linked source known-at date. Forward proposed trades, liability dates and other contractual assumptions remain distinct from observations.
