# Controls — portfolio-holdings-summarizer

- **Risk tier:** R1 — informational. **Action mode:** Read-only analysis.
- **Human approval:** `external-delivery` — required before the summary is delivered to a
  client or written to a system of record; not required for the user's own read.

## Prohibited (fail closed rather than do these)

- No investment **advice, recommendation, or opinion** on what to buy, sell, hold, or
  rebalance.
- No **suitability**, "good/bad", "well-diversified", "overweight/underweight", or
  risk-appropriateness judgment (that is advice; route elsewhere).
- No **price invention** for unpriced/stale lines; no **merging** of multiple accounts or
  as-of dates without explicit user confirmation.
- No **overriding** the position of record with a user assertion.

## Required "no-advice" language screen

`scripts/validate_output.py` scans the narrative for advice/recommendation phrasing
(buy/sell/recommend/should consider/overweight/underweight/too risky/we suggest/rebalance,
etc.). Any hit **fails closed**. A standing disclaimer must be present:
"Informational summary only; not investment advice or a recommendation."

## Data classification, privacy, records

- Classification: **Highly Confidential (customer NPI/PII)**.
- Mask account numbers to last 4 in all output. Keep holdings within the approved
  environment; never exfiltrate.
- Retain the snapshot + citations per records policy. Log: source read, snapshot creation,
  and any external-delivery approval (who/when).

## Reproducibility

Given the same position source and as-of date, the summary must be reproducible: the
`snapshot_id` binds the output to the exact inputs and citations used.
