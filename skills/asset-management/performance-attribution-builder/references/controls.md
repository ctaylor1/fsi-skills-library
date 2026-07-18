# Controls — performance-attribution-builder

- **Risk tier:** R2 — analytical / drafting support. **Action mode:** Draft-only; no
  system-of-record change. The output is a draft ex-post attribution for human review, not
  investment advice, a recommendation, a performance promise, or a delivery.
- **Human approval:** `external-delivery` — a human must review and approve before the attribution
  is used externally, in marketing/advertising, in a client report, or treated as a
  system-of-record change. Internal analytical assembly may be reviewer-sampled.

## Prohibited (fail closed)

- **Investment recommendation / advice**: any "we recommend", "you should buy/sell",
  "recommend increasing/reducing", "should overweight/underweight", or suitability statement.
  Attribution explains realized return; it does not advise. (Factual positioning language such as
  "the portfolio was overweight financials" is a description of what happened, not advice.)
- **Forward-looking / guaranteed performance**: any "will outperform", "guaranteed return",
  "expected to outperform", "projected to return", or promise about future returns. Attribution is
  ex-post only.
- **GIPS-compliance claim**: asserting the presentation or firm is "GIPS compliant" / "GIPS
  verified". GIPS compliance is a firm-wide claim requiring independent verification and is never
  asserted by this skill.
- **Unsubstantiated marketing**: superlatives such as "top-decile", "best-in-class returns",
  "number-one performing" presented without the required substantiation and disclosures.
- **Fabrication**: inventing a return, weight, or currency rate. A missing return makes the segment
  `needs-data` and its weight unattributed — never an assumed value.
- **Delivery / submission**: sending, distributing, publishing, or posting the attribution to a
  fact sheet, client, or investor. Draft-only.

## Build / segment states (this skill may set only these)

- Per segment: `attributed` | `needs-data` (missing a required return; weight unattributed).
- Reconciliation: `reconciled` | `residual-exceeds-tolerance`; official reconciliation per side:
  `reconciled` | `break`.
- Analysis: `draft-attribution` only. It may **not** set `final`, `approved`, `delivered`, or any
  performance-claim state.

## Required output screens (`scripts/validate_output.py`)

- All required template sections present (mirrors [../assets/output-template.md](../assets/output-template.md)).
- Every segment row carries a citation; every attributed segment ties out
  (`allocation + selection + interaction + currency == total`); the effect totals sum to the stated
  attributed active return; and `active_return == portfolio_return - benchmark_return`
  (no unsupported/unapproved claims).
- Recorded approvals carry `type`, `approver_role`, `date`, and `citation`; missing required
  approvals appear as outstanding open items; `human_approval_required_before_delivery` is `true`.
- No recommendation/advice, forward-looking/guaranteed-performance, GIPS-compliance,
  unsubstantiated-marketing, or send/deliver language.
- `build_status` equals `draft-attribution`.
- Standing note present (see [domain-rules.md](domain-rules.md)).

## Segregation of duties

Building the attribution is distinct from the performance-methodology sign-off, from the
compliance/marketing (SEC Marketing Rule) review, and from external delivery. The same person/skill
must not both assemble the attribution and sign off its methodology or deliver it to a client.

## Data classification, privacy, records

- **Highly Confidential (MNPI / client-confidential).** Holdings, weights, and returns can be
  client- or composite-confidential and potentially price-sensitive; mask approver and internal
  identifiers in output and enforce need-to-know.
- Retain the attribution manifest, citations, and config/template versions per the firm's
  performance-recordkeeping and (where applicable) GIPS/marketing recordkeeping policy; log the
  analyst identity on every read and build.
- Keep data within the deployment's residency boundary.
