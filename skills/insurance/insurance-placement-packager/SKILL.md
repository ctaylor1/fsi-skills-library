---
name: insurance-placement-packager
description: "Assemble a versioned insurance market-placement packet from a defined insured request, market responses, quoted terms and subjectivities. Use to reconcile market versions, identify comparable terms and prepare outstanding items for a broker or placement reviewer. Does not select a market, bind coverage, negotiate externally or treat a quote as issued insurance."
license: MIT
compatibility: Python 3.10+; offline structured evidence. No bundled production connectors or external execution.
metadata:
  aws-fsi-category: "Insurance"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Draft & package"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Insurance Phase 2"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "Reviewed target-specific jurisdiction/product profiles required; synthetic fixtures establish no local law"
  aws-fsi-owner: "Insurance distribution and sales supervision"
  aws-fsi-primary-user: "Broker placement / market operations reviewer"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-09-18"
---

# Insurance Placement Packager

Produce a source-linked draft for the accountable broker placement / market operations reviewer. For example: “Package these two carriers’ property quotes, preserve the superseded response and identify unresolved subjectivities for the broker.”

## Workflow

1. Establish the placement, insured, represented party, requested coverage, policy period and capacity. Resolve whether the user represents the insured, intermediary or insurer before using counterparties' material.
2. Retain every supplied market response with its original version and source. Distinguish a quote, decline and no response. If one market has multiple versions, require explicit identification of the current response; do not sort version strings or assume the lowest price is current.
3. Check response identity, issue/expiry dates and jurisdiction/line scope. For quotes, preserve currency, coverage basis, period, layer, limit, retention, covered interests and exclusions. Compare only identical stated bases; economic equivalence still needs professional review.
4. Reconcile premium, fees and taxes as separately sourced amounts. Unknown components remain unknown and suppress the total. Never mix currencies or annualize unlike periods silently.
5. Trace every subjectivity to its status and supporting evidence. Satisfied or carrier-waived assertions without evidence become unknown. Preserve open subjectivities in the reviewer packet; neither a satisfied checklist nor a displayed total binds the risk.
6. Draft a market comparison and outstanding-items schedule. Discuss material tradeoffs and unreviewed terms for the human broker; do not rank a winner solely by price. Keep external submission, negotiation, market selection and binding outside this package.

## Resources and deterministic work

Read [domain rules](references/domain-rules.md) for method limits, [source map](references/source-map.md) before asserting applicability, and [schema](references/schema.md) when normalizing evidence. Read [controls](references/controls.md) before preparing regulated decision support and [handoffs](references/handoffs.md) when the request crosses ownership.

Validate normalized input with `python scripts/validate_input.py input.json`; produce the immutable review record with `python scripts/calculate_or_transform.py input.json`; check that record with `python scripts/validate_output.py output.json`. A command exit of zero means the structure/evaluation ran, not that the case cleared. Inspect status, findings, completeness and evaluability. Run [regressions](scripts/test_workflow.py) for changed methods.

Use [the draft template](assets/output-template.md) to prepare the human review memo and [the worked synthetic input](evals/files/normal.json) for the exact native schema. Keep source_document attached; do not edit generated evidence statuses to make the packet appear ready. The bundled [insurance contract](references/insurance-contract.md) explains content binding and portable handoffs.

## Failure handling and acceptance

Missing business evidence should produce a useful gap packet; malformed inputs must be corrected. A source reference or evidence-present state does not establish authenticity, complete discovery, legal compliance or professional acceptance. Preserve disputed and adverse facts. Mandatory human adjudication remains distinct from software completeness. This release has offline regression coverage; live-source, professional and deployment acceptance are separate gates.

See [native workflow foundation](references/insurance-foundation.md) for source-bound context mappings, inherited uncertainty and output validation.
