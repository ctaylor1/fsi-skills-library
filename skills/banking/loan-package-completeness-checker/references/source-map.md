# Source Map — loan-package-completeness-checker

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | Loan **origination/closing system** (position of record) | Executed/received documents, their effective dates, signatures, conditions | Read-only |
| 2 | **Approval** record (AUS/credit decision output) | Approved amount, max rate, approval expiry — the envelope the package must sit within | Read-only |
| 3 | Controlled **checklist / register** (versioned) | Required document set, validity windows, required signers, per-jurisdiction items, severity mapping | Read-only |
| 4 | **Document intelligence** | Field extraction (amount, rate, borrower, address) and page/clause citations | Read-only |
| 5 | **Entity resolution** | Normalize borrower names, addresses, and counterparties for the consistency check | Read-only |

Never substitute an extracted value or a checklist assumption for the executed document of
record. If the origination system and an extracted field conflict, cite both and flag for
the certifier. Never infer a required-document set when the product/jurisdiction checklist is
absent — fail closed.

## Citation format

`{system}:{ref}@{date}` — e.g. `los:los=LN-2026-88213;doc=D-2@2026-03-01` for a document,
`checklist:checklist-conv-purchase-2026.06;item=CL-INCOME` for a checklist item, and
`condition:PTC-2` for a condition. Every finding cites the specific evidence it rests on.

## Freshness / effective dates

- The **checklist** (required set, validity windows, required signers, severity mapping) is a
  **versioned contract**; the assessment records `checklist_version` and `config_version` so a
  run is reproducible.
- **Expiration is measured to the package `as_of`** (the certification/closing date), not the
  clock time of the run. A document is expired when `as_of - effective_date > validity_days`.
- A document within `nearing_expiry_days` of its limit is an Advisory, not a Blocker; a
  document with a validity window but **no** `effective_date` is a **data gap** (not evaluable),
  never "valid".

## Least-privilege operations (deployment)

- `los.package(loan_id, package_type)` → documents, signatures, conditions, effective dates.
- `approval.get(loan_id)` → approved amount, max rate, approval expiry.
- `checklist.get(product, jurisdiction, version)` → required items + validity + signers.
- `docint.extract(doc_id, fields)` → normalized field values with page/clause citations.
- `entity.resolve(name|address)` → normalized entity for consistency comparison.

All read-only, deterministic, durable `assessment_id`, below the fixed timeout; page large
packages as resumable stages.
