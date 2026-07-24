# Controls — financial-document-version-comparator

- **Risk tier:** R2 — analytical. **Action mode:** Read-only analysis.
- **Human approval:** `external-delivery` — before external delivery.

## Prohibited (fail closed)
- No judgment of **legal significance, materiality, or disclosure sufficiency**.
- No **approval, editing, or publishing** of any version.
- No **invented section correspondence** when ids are missing; no fabricated diff of opaque content.

## Required output screen (`scripts/validate_output.py`)
- Every change carries a location (section id) + citation.
- No significance/materiality/approval/disclosure-sufficiency language (regex: is material/not
  material/materially/legally significant/approve(d) the document/disclosure is (adequate|
  sufficient)/we approved/publish the).
- Disposition is review-only (`clean` | `changes-for-review`).
- Standing disclaimer present.

## Data classification, privacy, records
- **Highly Confidential (MNPI / client-confidential).** Honor information barriers.
- Retain the change log + citations; log read + external-delivery approval.

## Reproducibility
`comparison_id` binds output to the exact two versions compared.
