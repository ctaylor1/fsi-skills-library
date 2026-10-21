# Native input and method

Common fields: request_id, object_id, as_of and knowledge_cutoff (real dates), currency, audience=internal-review and versioned sources[]. Each used observation carries a registered source_ref. Observation sources cannot be later than the review date or known after its cutoff. Scenarios are assumptions, not observed results.

Financial values accept decimal strings (preferred for exactness); <=38 coefficient digits and exponent/adjusted exponent +/-38. Exact operations run in a private precision256 context. Ratios explicitly round to12places; portfolio PSD uses1e-30 tolerance and100-digit arithmetic. Source restrictions and missing references reject input before values are emitted.

## Required domain fields and synthetic shape

```json
{
  "intended_audience": "institutional-client",
  "claims": [
    {
      "claim_id": "C1",
      "kind": "factual",
      "content": "The fund holds listed equities.",
      "source_ref": "S1"
    },
    {
      "claim_id": "BAD",
      "kind": "factual",
      "content": "UNSUPPORTED-SECRET-CLAIM",
      "source_ref": "S1"
    }
  ],
  "required_disclosures": [
    "D1"
  ],
  "disclosures": [
    {
      "id": "D1",
      "text": "Capital is at risk.",
      "source_ref": "S1"
    }
  ]
}
```

## Implemented algorithm

Review proposed investment communication claims against exact supplied approved source claims, intended audience, disclosures and performance presentation evidence. Withhold unsupported content and produce an internal compliance review; never approve or publish.

See the package calculator for exact field-level conventions; all fixture assumptions are synthetic and are not laws, recommended allocations or live prices. The fixture and independent-expectations file pair records independently computed numeric cases, not merely a regenerated golden.

## Unsupported scope

- Internal review packet; source approvals and rights remain supplied assertions.
- Bounded presentation checks do not determine legal marketing-rule compliance.

## Evidence and boundary clarification

If a claim or disclosure source declares object_id or currency, it must match the reviewed object and currency. Contradictory source scope withholds the content. Generic approved disclosures may omit those fields; that absence does not authenticate their relevance.

Actual price/market, acquisition/purchase and realized performance dates (where applicable) cannot exceed the review date, knowledge cutoff or linked source known-at date. Forward proposed trades, liability dates and other contractual assumptions remain distinct from observations.
