# Source Map — kyc-customer-due-diligence-screener

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **KYC/AML case system** (position of record for the CDD file) | Customer/entity attributes, documents, beneficial-owner declarations, identity checks | Read-only |
| 2 | **Sanctions & PEP screening** data | Potential sanctions/watchlist and PEP matches (indicators only) | Read-only |
| 3 | **Adverse-media** source | Adverse-media indicators (allegations, with source quality) | Read-only |
| 4 | **Beneficial-ownership / registry** reference data | Ownership chain, control persons, registry corroboration | Read-only |
| 5 | **Transaction monitoring** context (when a case exists) | Prior activity/typology context for the customer | Read-only |
| 6 | Financial-crime **config** (versioned) | Required fields/documents, thresholds, higher-risk country/industry lists | Read-only |

Never substitute a customer/applicant assertion for the record or the registry. A screening
indicator (sanctions/PEP/adverse-media) is a **potential match or allegation**, never a
disposition — the disposition is adjudicated by a specialist and a human. If the record, the
registry, and a screening source conflict, cite each and flag for the analyst.

## Citation format

`{system}:{ref}@{date}` — e.g. `kyc:case=KYC-2026-0042;owner=Alex Petrov@2026-07-15`,
`pep:case=KYC-2026-0042;party=Alex Petrov@2026-07-15`. Every fired signal cites the specific
record(s) or screening indicator(s) behind it and the `as_of` date.

## Freshness / effective dates

- Config (required fields/documents, thresholds, higher-risk lists) is a **versioned
  contract**; the output records the `config_version` used so a screening is reproducible.
- Document `expiry_date` is evaluated against `as_of`; jurisdiction-specific UBO thresholds
  and effective dates are configuration, not code.
- Screening indicators carry their own source date/quality; stale or low-quality indicators
  are labelled, never silently dropped.

## Least-privilege operations (deployment)

- `kyc.get_case(case_id)` → customer/entity attributes, documents, identity checks, owners.
- `screening.get(case_id, ['sanctions','pep','adverse_media'])` → potential indicators only.
- `registry.resolve(entity_id)` → ownership/control corroboration.
- `config.get('cdd', version)` → required fields/documents, thresholds, higher-risk lists.

All read-only, deterministic, durable `screening_id`, below the fixed timeout; page long
ownership chains or document sets as resumable stages. No write, adjudication, rating, or
filing operation is bound to this skill.
