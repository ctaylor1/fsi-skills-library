---
name: filing-disclosure-change-detector
description: "Compare supplied aligned filing sections and exhibit inventories for cited factual changes, including newly appearing restatement wording. Use for disclosure-change evidence; missing inventories stay not evaluable and no materiality or thesis conclusion is made."
license: MIT
compatibility: Amazon Quick Desktop; requires filed-form retrieval (EDGAR/regulator filing store), document-intelligence, entity-resolution, and versioned change-detection config MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Investment Research"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 5 - 2026 industry expansion"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "existing-updated"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (MNPI / client-confidential)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Investment Research"
  aws-fsi-primary-user: "Research associate"
  aws-fsi-version: "0.3.0"
  aws-fsi-recertification-date: "2027-10-20"
---

# filing-disclosure-change-detector

Locate factual changes in supplied structured filing inventories and fan findings out to human review lanes. It does not parse filings or determine whether a restatement occurred.

Use this package for its supplied-input job. Requests for missing source retrieval, professional conclusions, live actions or distribution require the separately provisioned owner and access. Read [native contract](references/phase1-contract.md) before preparing inputs and [controls](references/controls.md) before using results.

## Native operation

1. Establish issuer/document/market identity, permitted purpose and audience. Retain the original supplied JSON separately.
2. Run `python3 -B scripts/validate_input.py INPUT.json`. Missing evidence is never filled from fixtures.
3. Run `python3 -B scripts/calculate_or_transform.py INPUT.json` to produce native JSON.
4. Run `python3 -B scripts/validate_output.py OUTPUT.json --input INPUT.json`. No output-only validation, embedded source snapshot or extra narrative is supported. `--selftest` uses the retained example input and refreshed golden result.
5. Review partial/not-evaluable fields and unresolved items before preparing an audience-specific narrative separately. A reconstructed result does not authenticate sources, grant access or establish professional acceptance.

## Boundaries and handoffs

Generic document comparison can supply reviewed alignment but has a different native schema. Financial-reporting/legal reviewers interpret flagged wording and contract changes. Thesis reassessment needs an actual thesis/version and analytical review; this detector supplies facts, not investment implications.

Read [handoffs](references/handoffs.md), [sources](references/source-map.md) and [domain method](references/domain-rules.md). Offline JSON operations are implemented; live connectors, verified entitlements, institutional policies and professional acceptance are deployment dependencies. Package hashes establish reproducibility only.

## Shared Phase 1 evidence standard

Read [the evidence and control standard](references/evidence-standard.md) for identity,
knowledge timing, permission use, detached source binding and professional acceptance
boundaries. The package retains its native schema; no universal adapter is implied.

## Phase 2 native analysis

For `schema_version: ir-phase2/1.0`, read [the analytical intake and method](references/phase2-contract.md). This expands the method with source eligibility, basis and timing controls through the supplied-evidence analysis contract. Legacy Phase 1 inputs retain their existing interface. Both modes require the separately retained original for full output reconstruction. A reviewed adapter validates producer and receiver; a supplied status label is not an approval.
