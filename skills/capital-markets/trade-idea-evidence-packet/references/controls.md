# Controls — trade-idea-evidence-packet

- **Risk tier:** R3 — regulated/control decision support. **Action mode:** Draft-only; no
  system-of-record change.
- **Human approval:** `required` — for any recommendation to a specific client, suitability/
  eligibility determination, or investment advice.

## Prohibited (fail closed)
- No **recommendation to any specific client**; no **investment advice**.
- No **suitability/eligibility determination** — flags are surfaced, not adjudicated.
- No **presenting uncited claims as evidence**; no clearing a restricted product.

## Required output screen (`scripts/validate_output.py`)
- Every data point carries a citation; every gap/flag carries a citation.
- No client-recommendation/suitability language (regex: recommend to client/suitable for
  client/we recommend buying/you should buy/is suitable for/advise the client to/tailored
  recommendation).
- Suggested disposition is review-only (`packet-ready` | `gaps-for-review`).
- Standing disclaimer present.

## Segregation of duties
The packet preparer is not the distribution/suitability authority; the packet supports internal
review, never replaces the human/compliance decision to distribute or determine suitability.

## Data classification, privacy, records
- **Highly Confidential (customer NPI/PII).** Keep the packet idea-level and internal.
- Retain packet + citations; log read + external-delivery approval; enforce information barriers.

## Reproducibility
`packet_id` binds output to the exact idea, data points, and config version.
