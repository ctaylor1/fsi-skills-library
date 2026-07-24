# Changelog — bank-product-feature-comparator

## [0.1.0] — 2026-07-20
Initial authoring in the FSI Skills Library (2026 industry-expansion cohort, Wave 5). Baseline
status `new` (no prior AWS baseline artifact).

- **Scope:** neutral, source-cited side-by-side comparison of two or more **approved** bank
  products across eligibility, fees, features, disclosures, and effective dates, plus the
  outstanding discovery questions the relationship banker must confirm and a citation index.
  Read-only; no needs assessment, no suitability call, no recommendation or ranking.
- **Freshness/approval gate (deterministic, fail closed):** a requested product is compared
  only if approved, effective, not expired, and not superseded as of `as_of`; any stale,
  unapproved, not-yet-effective, or unknown product fails the whole comparison closed with
  `block_reasons` + `required_action` (see `scripts/calculate_or_transform.py`).
- **Controls:** R2; hard boundary against needs assessment, suitability determination, and
  product recommendation/ranking; approved-catalog content only; `external-delivery` approval.
- **Scripts:** `validate_input` (request/product schema, unknown-product + citation-gap
  checks), comparison engine (gate + neutral cited side-by-side + citation index + discovery
  questions), `validate_output` (R2 recommendation/suitability screen, stale/unapproved leak
  screen, citation completeness, fail-closed integrity, disclaimer). Each script self-tests
  over bundled de-identified fixtures.
- **Evaluations:** trigger/routing, golden `ok` and golden `fail_closed` (stale) cases,
  deterministic script checks, no-recommendation + unknown-product safety fixtures (fail
  closed), prompt-injection and external-delivery authorization behaviors.
- **Handoffs:** downstream to `suitability-reg-bi-reviewer` (recommendation review),
  `commercial-cash-management-advisor` (commercial services advisory), `fee-and-charge-reviewer`
  (existing-account posted fees), `customer-onboarding-document-checker` (open/onboard); human
  handoff to the product-content owner on stale/unapproved content.

### Pending before release
- Domain SME (product & marketing-compliance) + control-owner blind review; conduct/fair-
  comparison review of neutrality wording.
- Confirm the versioned product-catalog source, its owner, and the freshness/effective-date
  service contract.
- Wire read-only MCP integrations (content library/product catalog, disclosure retrieval,
  entity resolution, freshness) at deployment.
