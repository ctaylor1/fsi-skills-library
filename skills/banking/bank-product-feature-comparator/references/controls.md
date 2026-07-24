# Controls — bank-product-feature-comparator

- **Risk tier:** R2 — analytical. **Action mode:** Read-only analysis.
- **Human approval:** `external-delivery` — required before the comparison is delivered to a
  customer or written to a case/system of record. No approval is needed for the banker's own
  read.

## Prohibited (fail closed)

- **No needs assessment.** Do not infer, score, or characterize the customer's needs, goals,
  risk tolerance, or financial situation.
- **No suitability determination.** Do not state or imply that a product is or is not
  suitable, appropriate, or a good fit for the customer.
- **No recommendation or ranking.** Do not recommend, suggest, prefer, rank, pick a "best"
  or "better" product, or declare a winner. Present cited facts side by side only.
- **No unapproved or stale content.** If any requested product is not `approved`, is
  not yet effective, is expired, or is superseded, **fail closed**: emit no comparison, list
  the blocking reasons and the required content action.
- **No fabricated or uncited attributes.** Every compared value cites an approved-source
  record + effective date. Missing terms are labeled a data gap, never guessed.

## Required output screens (`scripts/validate_output.py`)

- **Recommendation/suitability screen** (free text + structural fields): no advice/ranking
  language and no `recommended_product` / `best_product` / `winner` / `ranking` /
  `preferred_product` fields or per-cell `winner`/`preferred` flags. This is the R2
  prohibited-decision screen; a non-compliant pack fails closed (exit 1).
- **Stale/unapproved leak screen:** a `status: ok` pack with any `excluded` product is an
  error (stale/unapproved content must not appear in a comparison).
- **Citation completeness:** every present comparison cell has a citation; every compared
  product appears in the `citation_index`.
- **Comparison integrity:** `status: ok` requires >= 2 approved products and >= 1
  outstanding discovery question; `status: fail_closed` requires `block_reasons` and an
  empty comparison.
- **Standing disclaimer present:** "Factual comparison of approved products only. This is not
  advice, a suitability assessment, or a product recommendation. Confirm current product
  terms and the customer's eligibility before proceeding."

## Fairness / conduct

- Compare products, not customers. Do not use or infer protected-class attributes.
- Describe fees, features, and eligibility factually and symmetrically; do not editorialize
  ("only", "just", "unbeatable", "cheap", "expensive") — state the number and cite it.

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII).** In practice this skill needs little customer
  data — it compares product content. Do not pull customer profile/needs data.
- Retain the comparison + `citation_index` + `approved_catalog_version` per records policy;
  log the read and any external-delivery approval.

## Reproducibility

`request_id` binds the pack to the exact requested products, `as_of`, and
`approved_catalog_version`; re-running with the same inputs and catalog version reproduces
the comparison, the citation index, and any fail-closed decision.
