---
name: bank-product-feature-comparator
description: >-
  Produce a neutral, source-cited side-by-side comparison of two or more APPROVED bank
  products across eligibility, fees, features, disclosures, and effective dates, plus the
  outstanding discovery questions the relationship banker still needs to confirm with the
  customer, and a citation index. Use when a banker asks to "compare these checking/savings
  products", "what's different between Product A and Product B", "put these approved products
  side by side", or needs a factual, review-ready comparison with citations. HARD BOUNDARY:
  never assess customer needs, judge suitability, or recommend, rank, or pick a
  "best"/"better" product; fail closed on any stale, superseded, unapproved, not-yet-effective,
  or unknown product content (emit no comparison; list the block reason). Read-only; not
  advice or a suitability determination. Route recommendation review to a human and to
  investment-recommendation-evidence-reviewer.
license: MIT
compatibility: Amazon Quick Desktop; requires controlled-content-library/product-catalog, approved-disclosure-retrieval, entity-resolution, and data-governance freshness MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Banking"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 5 - 2026 industry expansion"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Banking product & credit operations"
  aws-fsi-primary-user: "Relationship banker"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Bank Product Feature Comparator

## Purpose and outcome
Given two or more **approved** bank products and an `as_of` date, produce a **neutral,
source-cited side-by-side comparison** across eligibility, fees, features, disclosures, and
effective dates, together with the **outstanding discovery questions** the relationship
banker still needs to confirm with the customer and a **citation index**. A successful output
lets a banker see exactly how approved products differ, with every value traceable to a
current, approved record — so the banker (a human) can have an accurate, compliant
conversation. The comparison **never** assesses needs, judges suitability, or recommends a
product.

## Use when
- "Compare Essential Checking and Premier Interest Checking for me."
- "What's different between these two approved savings products?"
- "Put these products side by side — fees, features, eligibility, disclosures."
- A banker needs a consistent, cited comparison to reference in a client conversation or to
  attach (after approval) to a customer communication.

## Do not use
- The user wants a **recommendation, suitability call, or needs assessment** ("which should
  the customer pick?", "which is best for them?", "is this suitable?") → **out of scope**.
  Present the factual comparison only; the human decides, and a documented recommendation
  goes to `investment-recommendation-evidence-reviewer`.
- The user wants **treasury/cash-management services recommended** from a commercial
  customer's cash flows → `commercial-cash-management-advisor`.
- The user wants a **specific existing account's posted fees** identified and compared to
  disclosed terms (not published product sheets) → `fee-and-charge-reviewer`.
- The customer has chosen a product and wants to **open/onboard** it →
  `customer-onboarding-document-checker`.
- Any requested product is **unapproved, stale, superseded, not yet effective, or unknown**
  → fail closed (do not compare); route the content owner to refresh/approve it.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a comparison + citation
index with a durable `request_id`; downstream review/advisory/onboarding skills consume it.
It must not duplicate their recommendation, suitability, or onboarding work.

## Inputs and prerequisites
- A **comparison request** naming >= 2 product identifiers to compare, an `as_of` date, and
  the `approved_catalog_version`.
- **Approved product records** for each requested product, each with `approval_status`,
  `effective_date`, optional `expiry_date`/`superseded_by`, `version`, `source_ref`,
  `attributes` (eligibility / fees / features, each row cited), `disclosures`, and
  `discovery_questions`. Schema: [scripts/validate_input.py](scripts/validate_input.py).
- Read access to the controlled content library / product catalog and disclosure retrieval
  (see [references/source-map.md](references/source-map.md)). No customer profile/needs data
  is required or used.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The controlled product catalog is
the position of record; approved disclosures and entity resolution support it; the freshness
service confirms currency. A marketing page, screenshot, prior comparison, or customer
recollection is **not** an approved source. Cite every value to a versioned record + effective
date.

## Workflow
1. **Scope** — confirm the >= 2 products, `as_of`, and catalog version; validate the request
   with `validate_input`.
2. **Freshness/approval gate (deterministic, fail closed)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py). For each requested
   product it checks approved + effective + not expired + not superseded. If **any** product
   is unusable, it returns `status: "fail_closed"` with `block_reasons` and a
   `required_action` — **stop and route the content owner**; emit no comparison.
3. **Build the comparison (only if all usable)** — the engine emits a neutral side-by-side
   across eligibility, fees, and features (attribute names taken verbatim; missing terms
   labeled a data gap), a `disclosures_index`, `effective_dates`, and a `citation_index`.
4. **Surface discovery questions** — the union of each product's factual `discovery_questions`
   the banker must confirm with the customer (fact-gathering, not suitability).
5. **Validate & present** — run [scripts/validate_output.py](scripts/validate_output.py); on
   pass, present the comparison, citation index, discovery questions, and data gaps with the
   standing disclaimer.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check confirms: no recommendation/suitability/ranking language or fields
(the R2 prohibited-decision screen), no stale/unapproved product leaked into an `ok`
comparison, every present cell cited, every compared product in the citation index, >= 2
products and >= 1 discovery question, a well-formed fail-closed pack when blocked, and the
disclaimer present. Fail closed on any miss.

## Human approval
`external-delivery`: human review required before the comparison is delivered to a customer or
written to a case/system of record. No approval is needed for the banker's own read. The skill
takes no product action and makes no recommendation.

## Failure handling
- **Unapproved / stale / superseded / not-yet-effective / unknown product** → `fail_closed`:
  no comparison; list the block reason; route the content owner to refresh/approve. Never
  work around the block.
- **Ambiguous product identity** → stop and confirm the canonical `product_id`; never compare
  the wrong product.
- **Missing attribute on one product** → mark the cell a data gap ("not specified on this
  product's approved sheet"); never infer the value.
- **Missing citations** → the value is not usable; treat as a data gap, do not present
  uncited terms as fact.
- **Only one usable product** → not a comparison; stop and ask for a second approved product.
- **Tool timeout** → return the products gated/compared so far with a clear "incomplete" flag;
  do not assume a retry.

## Output contract
1. **Summary** — request, `as_of`, catalog version, products compared (or blocked), status.
2. **Comparison** — per attribute (grouped by eligibility / fees / features): each product's
   cited value side by side, with data-gap cells labeled. **No ranking, no winner.**
3. **Disclosures & effective dates** — per product, cited.
4. **Outstanding discovery questions** — factual items the banker must confirm with the
   customer.
5. **Data gaps** — attributes a product's approved sheet does not specify.
6. **Citation index** — every cited value → product version + effective date.
7. **Machine-readable** — the full pack + `request_id` for downstream skills.
8. **Standing disclaimer** — "Factual comparison of approved products only. This is not
   advice, a suitability assessment, or a product recommendation. Confirm current product
   terms and the customer's eligibility before proceeding."
See [references/controls.md](references/controls.md).

## Privacy and records
Highly Confidential context, but this skill compares **product content**, not customer data —
do not pull customer profile/needs data. Retain the comparison + `citation_index` +
`approved_catalog_version` per records policy; log the read and any external-delivery
approval. Never present unapproved or stale terms.

## Gotchas
- **A comparison is not a recommendation.** Showing that Product B has a lower fee is a fact;
  saying it is "better for the customer" is a prohibited suitability/recommendation call.
- **Stale content misleads.** A lapsed disclosure or an expired/superseded fee schedule can
  quietly be wrong — the freshness gate fails closed for exactly this reason; do not override.
- **Symmetry matters.** Present both/all products with the same attributes and neutral
  wording; do not foreground one product's advantages.
- **Discovery questions are fact-gathering, not scoring.** List what the banker must confirm;
  do not evaluate the answers or infer needs from them.
- **Never fill a data gap by inference.** If an approved sheet is silent on an attribute, say
  so and cite the gap; do not borrow the other product's value or a marketing page.
- **Approved set only.** Compare only products the catalog returns as approved for this
  banker; never add a product from memory, a prior deal, or a customer's suggestion.
