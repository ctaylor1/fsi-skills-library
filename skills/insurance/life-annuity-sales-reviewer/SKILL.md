---
name: life-annuity-sales-reviewer
description: "Prepare a product- and capacity-specific life or annuity sales review from consumer needs, alternatives, product costs, guarantees, disclosures and replacement evidence. Use for pre-sale supervisory review or replacement case preparation. Exposes missing evidence and rule-applicability questions; does not recommend a sale, score suitability, approve best interest, execute an exchange or certify compliance."
license: MIT
compatibility: Python 3.10+; offline structured evidence. No bundled production connectors or external execution.
metadata:
  aws-fsi-category: "Insurance"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Insurance Phase 2"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "Reviewed target-specific jurisdiction/product profiles required; synthetic fixtures establish no local law"
  aws-fsi-owner: "Insurance distribution and sales supervision"
  aws-fsi-primary-user: "Life/annuity sales supervision / compliance reviewer"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-09-18"
---

# Life and Annuity Sales Evidence Review

Produce a source-linked draft for the accountable life/annuity sales supervision / compliance reviewer. For example: “Prepare a replacement review comparing the customer’s existing permanent policy with the proposal, including lost guarantees, funding needs, alternatives and missing evidence.”

## Workflow

1. Establish the customer's objective, recommending capacity, product classification, distribution channel and jurisdiction. Keep fixed, indexed, deferred variable annuity, variable life and other life products distinct; product naming alone does not resolve legal classification.
2. Obtain the reviewed applicability profile, including enacted jurisdiction requirements, product-specific regulator rules and institution policy. Distinguish model text from adopted law. Record each rule's source, scope and rationale; do not apply FINRA deferred variable annuity rules to all insurance products.
3. Build a source-linked consumer evidence matrix covering needs, objectives, financial capacity, liquidity, funding, age, time horizon, risk tolerance, experience and tax situation. Add the profile's product-specific fields; retain contradictory or refused data explicitly rather than assuming a favorable value.
4. Compare the proposed product's charges, surrender terms, restrictions, guaranteed and non-guaranteed elements, death benefit and product-specific obligations. Trace compensation/conflicts, training and disclosures to the supplied records. An evidence-present label means a reviewed summary was supplied, not that the transaction satisfies a legal standard.
5. Document considered alternatives and the basis of the supplied recommendation. Establish whether existing policy values, loans, surrenders or financed purchases create a replacement question. Where replacement is indicated, compare current values/benefits/charges, lost guarantees, new charges and surrender period, and retaining or modifying existing coverage.
6. Draft a case-specific reviewer memo separating supported observations, contrary evidence, missing items and the unresolved decision. Tax conclusions, underwriting acceptance, licensed recommendations, principal approval and carrier issuance remain outside this package.

## Resources and deterministic work

Read [domain rules](references/domain-rules.md) for method limits, [source map](references/source-map.md) before asserting applicability, and [schema](references/schema.md) when normalizing evidence. Read [controls](references/controls.md) before preparing regulated decision support and [handoffs](references/handoffs.md) when the request crosses ownership.

Validate normalized input with `python scripts/validate_input.py input.json`; produce the immutable review record with `python scripts/calculate_or_transform.py input.json`; check that record with `python scripts/validate_output.py output.json`. A command exit of zero means the structure/evaluation ran, not that the case cleared. Inspect status, findings, completeness and evaluability. Run [regressions](scripts/test_workflow.py) for changed methods.

Use [the draft template](assets/output-template.md) to prepare the human review memo and [the worked synthetic input](evals/files/normal.json) for the exact native schema. Keep source_document attached; do not edit generated evidence statuses to make the packet appear ready. The bundled [insurance contract](references/insurance-contract.md) explains content binding and portable handoffs.

## Failure handling and acceptance

Missing business evidence should produce a useful gap packet; malformed inputs must be corrected. A source reference or evidence-present state does not establish authenticity, complete discovery, legal compliance or professional acceptance. Preserve disputed and adverse facts. Mandatory human adjudication remains distinct from software completeness. This release has offline regression coverage; live-source, professional and deployment acceptance are separate gates.

See [native workflow foundation](references/insurance-foundation.md) for source-bound context mappings, inherited uncertainty and output validation.
