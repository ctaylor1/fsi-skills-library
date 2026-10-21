# Native input and method

Common fields: request_id, object_id, as_of and knowledge_cutoff (real dates), currency, audience=internal-review and versioned sources[]. Each used observation carries a registered source_ref. Observation sources cannot be later than the review date or known after its cutoff. Scenarios are assumptions, not observed results.

Financial values accept decimal strings (preferred for exactness); <=38 coefficient digits and exponent/adjusted exponent +/-38. Exact operations run in a private precision256 context. Ratios explicitly round to12places; portfolio PSD uses1e-30 tolerance and100-digit arithmetic. Source restrictions and missing references reject input before values are emitted.

## Required domain fields and synthetic shape

```json
{
  "assets": [
    {
      "id": "EQ",
      "group": "equity",
      "expected_return": ".08",
      "liquidity_days": 1,
      "source_ref": "S1"
    },
    {
      "id": "BOND",
      "group": "bonds",
      "expected_return": ".03",
      "liquidity_days": 1,
      "source_ref": "S1"
    }
  ],
  "covariance": [
    [
      ".04",
      ".006"
    ],
    [
      ".006",
      ".01"
    ]
  ],
  "covariance_source_ref": "S1",
  "candidates": [
    {
      "id": "balanced",
      "weights": {
        "EQ": ".6",
        "BOND": ".4"
      }
    }
  ],
  "constraints": {
    "group_ranges": {
      "equity": {
        "min": ".4",
        "max": ".8"
      }
    },
    "max_position": ".7",
    "minimum_expected_return": ".055",
    "maximum_volatility": ".2"
  },
  "scenarios": [
    {
      "id": "down",
      "asset_returns": {
        "EQ": "-.2",
        "BOND": ".05"
      },
      "source_ref": "S1"
    }
  ],
  "universe_type": "asset_class"
}
```

## Implemented algorithm

Compare supplied strategic or tactical institutional allocation alternatives against objectives, covariance, liquidity and scenario constraints. Produce a draft comparison; optimization requires a separately accepted engine.

See the package calculator for exact field-level conventions; all fixture assumptions are synthetic and are not laws, recommended allocations or live prices. The fixture and independent-expectations file pair records independently computed numeric cases, not merely a regenerated golden.

## Unsupported scope

- Annualized supplied covariance; PSD tolerance1e-30 and analytic volatility rounded12places.
- No shorting/leverage, nonlinear derivatives, liability optimization or solver; expected returns are assumptions.

## Evidence and boundary clarification

Asset observations, the covariance matrix and each scenario require explicit source references. Candidate weights and constraints are caller-supplied modeling choices. Volatility constraints compare exact variance against the squared nonnegative limit; display rounding never controls feasibility.
