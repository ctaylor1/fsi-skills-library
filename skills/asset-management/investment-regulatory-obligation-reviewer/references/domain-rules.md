# Native input and method

Common fields: request_id, object_id, as_of and knowledge_cutoff (real dates), currency, audience=internal-review and versioned sources[]. Each used observation carries a registered source_ref. Observation sources cannot be later than the review date or known after its cutoff. Scenarios are assumptions, not observed results.

Financial values accept decimal strings (preferred for exactness); <=38 coefficient digits and exponent/adjusted exponent +/-38. Exact operations run in a private precision256 context. Ratios explicitly round to12places; portfolio PSD uses1e-30 tolerance and100-digit arithmetic. Source restrictions and missing references reject input before values are emitted.

## Required domain fields and synthetic shape

```json
{
  "jurisdictions": [
    "US"
  ],
  "entity_facts": {
    "registration": "SEC",
    "private_fund_assets": "100"
  },
  "rules": [
    {
      "rule_id": "SYNTHETIC-REVIEW",
      "version": "1",
      "reviewer": "Legal",
      "review_status": "reviewed",
      "jurisdiction": "US",
      "effective_from": "2026-01-01",
      "status": "final",
      "predicates": [
        {
          "fact": "registration",
          "operator": "eq",
          "value": "SEC"
        },
        {
          "fact": "private_fund_assets",
          "operator": "gte",
          "value": "50"
        }
      ],
      "due_date": "2026-09-20",
      "completion_status": "open",
      "owner": "Compliance",
      "source_ref": "S1"
    }
  ]
}
```

## Implemented algorithm

Evaluate a supplied reviewed investment rule pack against explicit entity facts, jurisdiction, activities and effective dates. Separate applicable, inapplicable, proposed and unresolved obligations; never infer a legal conclusion or certify compliance.

See the package calculator for exact field-level conventions; all fixture assumptions are synthetic and are not laws, recommended allocations or live prices. The fixture and independent-expectations file pair records independently computed numeric cases, not merely a regenerated golden.

## Unsupported scope

- Synthetic eval thresholds are not law; deploy only reviewed current primary rule packs.
- No universal legal interpretation, regulatory filing or compliance certification.

## Evidence and boundary clarification

An applicable obligation without an owner remains unresolved. A caller completion_status=completed is retained as supplied-unverified and never suppresses a past-due review flag; the accountable reviewer must inspect completion evidence and determine discharge. No automated completion acceptance is implemented.
