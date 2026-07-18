# Source Map — customer-onboarding-document-checker

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Document intelligence** (imaged docs, extracted fields) | Document presence, type, dates, signature blocks, field values | Read-only |
| 2 | **Core banking / onboarding case** (system of record) | Package identity, applicant record, product, jurisdiction, open exceptions | Read-only |
| 3 | **CRM** | Applicant-declared details, prior relationship context, known aliases | Read-only |
| 4 | **Loan origination/servicing** (when the package is credit-linked) | Required-document checklist for the credit product | Read-only |
| 5 | **Product terms / controlled register** (versioned) | Which documents are required per customer type, product, and jurisdiction | Read-only |
| 6 | Onboarding **config** (versioned) | Checklist, key identity fields, staleness/expiry thresholds, severities | Read-only |

The **imaged/extracted document** is the evidence of what was actually collected; the
**onboarding case** is the position of record for the applicant and exceptions. If an
extracted field and the applicant record conflict, cite both and raise a
`data_inconsistency` finding — never silently reconcile.

## Citation format

`{system}:{ref}@{date}` — e.g. `docs:pkg=CDC-2026-0442;doc=D-1@2025-01-01`,
`config:onboarding-cfg-2026.07;required=signature_card`,
`exceptions:pkg=CDC-2026-0442;exc=E-1`. Every fired finding cites the specific document,
field, config requirement, or exception behind it.

## Freshness / effective dates

- The required-document **checklist** (per customer type / product / jurisdiction) and the
  **severities** are a versioned contract; the output records the `config_version` used so
  a check is reproducible.
- Document **expiration** and **staleness** are evaluated against the package `as_of` date,
  which the output states explicitly.
- A jurisdiction pack change (e.g., new CIP document requirement) is a config change, not a
  code change; re-run reproduces the new checklist.

## Least-privilege operations (deployment)

- `docintel.get(package_id)` → document list with type, status, dates, signature flags, and
  extracted fields.
- `onboarding.case(package_id)` → applicant record, product, jurisdiction, open exceptions.
- `crm.context(customer_id)` → declared details and known aliases (no free-text PII beyond
  what evidences a finding).
- `config.get('onboarding', version)` → checklist + key fields + thresholds + severities.

All read-only, deterministic, durable `checklist_id`, below the fixed timeout; page large
document sets as resumable stages.
