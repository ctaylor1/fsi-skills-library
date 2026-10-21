# Native input and method

Common fields: request_id, object_id, as_of and knowledge_cutoff (real dates), currency, audience=internal-review and versioned sources[]. Each used observation carries a registered source_ref. Observation sources cannot be later than the review date or known after its cutoff. Scenarios are assumptions, not observed results.

Financial values accept decimal strings (preferred for exactness); <=38 coefficient digits and exponent/adjusted exponent +/-38. Exact operations run in a private precision256 context. Ratios explicitly round to12places; portfolio PSD uses1e-30 tolerance and100-digit arithmetic. Source restrictions and missing references reject input before values are emitted.

## Required domain fields and synthetic shape

```json
{
  "institution_type": "endowment",
  "objectives": {
    "return_objective": "CPI+4% over rolling5years",
    "risk_tolerance": "20% drawdown review trigger",
    "horizon_years": 20,
    "tax_status": "supplied exempt determination",
    "legal_constraints": "executed mandate v2",
    "spending_policy": "annual4% of trailing NAV",
    "source_ref": "S1"
  },
  "constraints": {
    "allocation_ranges": [
      {
        "asset_class": "equity",
        "minimum": ".4",
        "maximum": ".8"
      },
      {
        "asset_class": "bonds",
        "minimum": ".2",
        "maximum": ".6"
      }
    ],
    "liquidity_reserve": "20",
    "dated_outflows": [
      {
        "date": "2026-12-01",
        "amount": "25",
        "source_ref": "S1"
      }
    ]
  },
  "governance": {
    "investment_owner": "CIO",
    "risk_owner": "Risk",
    "review_owner": "Committee",
    "approval_owner": "Board"
  },
  "benchmark": {
    "id": "POLICY",
    "version": "2",
    "source_ref": "S1"
  }
}
```

## Implemented algorithm

Prepare an institutional investment policy draft from explicit asset-owner objectives, liquidity needs, allocation ranges and governance. Detect contradictory ranges and missing owners; household advice remains in Wealth Management.

See the package calculator for exact field-level conventions; all fixture assumptions are synthetic and are not laws, recommended allocations or live prices. The fixture and independent-expectations file pair records independently computed numeric cases, not merely a regenerated golden.

## Unsupported scope

- No optimization, suitability determination or policy adoption.
- Liquidity outflows are supplied; uncertain liabilities require separate modeling.

## Evidence and boundary clarification

The objectives source_ref explicitly covers the supplied policy objectives, constraints and named governance; each dated outflow and benchmark requires its own source_ref. A populated registry without these links is invalid.
