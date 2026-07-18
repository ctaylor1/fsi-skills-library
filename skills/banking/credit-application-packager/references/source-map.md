# Source Map — credit-application-packager

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Loan origination / servicing (LOS)** | System of record for the application, `package_id`, recorded approvals, conditions | Read-only |
| 2 | **Document intelligence** | Underlying documents (financials, tax returns, collateral, appraisals), page/field citations, effective/expiration dates | Read-only |
| 3 | **Core banking** | Account/relationship data, KYC/onboarding artifacts | Read-only |
| 4 | **CRM** | Borrower profile, entity, relationship context | Read-only |
| 5 | **Product terms** | `required_components` and `required_approvals` per product/jurisdiction (versioned) | Read-only |
| 6 | **Approved calculation service** | Any figures re-derived for the index (deterministic, cited) | Read-only |

The LOS state (application, approvals, conditions) wins on conflict; document intelligence
provides the evidencing artifacts. Product terms are the authority on what the package must
contain. This skill reads only — it never writes back an assembly, decision, or delivery.

## Citation format

`{system}:{ref}@{date/version}` — e.g. `los:doc=D-APP-1@2026-07-01`,
`docintel:doc=D-FS-1@2026-03-31`, `los:approval=AP-1@2026-07-10`,
`config:product-terms@2026.07`. Every `included`, `stale`, or `unresolved` item in the
package carries a citation; a component with no citable source is an `open-item`, never an
assumed inclusion.

## Freshness / effective dates

- Each document carries `effective_date` and optional `expires`. A document past its
  `expires` relative to `as_of_date` is marked `stale` and listed as an open item for
  refresh — it is still cited, never dropped.
- `required_components`, `required_approvals`, and the package template are **versioned
  contracts**; the versions are recorded on the manifest (`config_version`,
  `template_version`) for reproducibility and review.

## Least-privilege operations (deployment)

- `los.read(package_id)` → application, approvals, conditions — read-only.
- `docintel.get(doc_id)` / `docintel.cite(doc_id, field)` → documents + citations — read-only.
- `core.read(borrower_id)`, `crm.read(borrower_id)` → identity/relationship — read-only.
- `product_terms.get(product, jurisdiction, version)` → required components/approvals — read-only.
No mutation from this skill. The assembled package is a **draft**; any delivery or
system-of-record change is a separate, human-approved step via the approval broker.
