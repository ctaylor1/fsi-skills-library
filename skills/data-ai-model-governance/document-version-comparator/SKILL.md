---
name: document-version-comparator
description: "Compare two supplied structured document versions for section, heading, order, exact text and explicit value changes. Use for a bounded change register; duplicate IDs fail, omitted value inventories stay not evaluable and extraction completeness/materiality remain unverified."
license: MIT
compatibility: Amazon Quick Desktop; requires document-intelligence and controlled document-repository MCP integrations (read-only); bundled scripts are stdlib-only over structured document JSON.
metadata:
  aws-fsi-category: "Data, AI & Model Governance"
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
  aws-fsi-owner: "Data, AI & Model Governance"
  aws-fsi-primary-user: "Document analyst"
  aws-fsi-version: "0.2.0"
  aws-fsi-recertification-date: "2027-10-20"
---

# document-version-comparator

Locate changes in supplied structured versions. This generic comparison method is owned by Data, AI & Model Governance; issuer-specific disclosure analysis remains with filing-disclosure-change-detector. Legacy identifiers resolve through the migration registry.

Use this package for its supplied-input job. Requests for missing source retrieval, professional conclusions, live actions or distribution require the separately provisioned owner and access. Read [native contract](references/phase1-contract.md) before preparing inputs and [controls](references/controls.md) before using results.

## Native operation

1. Establish issuer/document/market identity, permitted purpose and audience. Retain the original supplied JSON separately.
2. Run `python3 -B scripts/validate_input.py INPUT.json`. Missing evidence is never filled from fixtures.
3. Run `python3 -B scripts/calculate_or_transform.py INPUT.json` to produce native JSON.
4. Run `python3 -B scripts/validate_output.py OUTPUT.json --input INPUT.json`. No output-only validation, embedded source snapshot or extra narrative is supported. `--selftest` uses the retained example input and refreshed golden result.
5. Review partial/not-evaluable fields and unresolved items before preparing an audience-specific narrative separately. A reconstructed result does not authenticate sources, grant access or establish professional acceptance.

## Boundaries and handoffs

Approved extraction and document control own the original versions and alignment. Filing-specific review, model continuity and credit-document interpretation remain separate. Human reviewers decide completeness, significance and any document change; this utility does not edit, approve or publish.

Read [handoffs](references/handoffs.md), [sources](references/source-map.md) and [domain method](references/domain-rules.md). Offline JSON operations are implemented; live connectors, verified entitlements, institutional policies and professional acceptance are deployment dependencies. Package hashes establish reproducibility only.

## Shared Phase 1 evidence standard

Read [the evidence and control standard](references/evidence-standard.md) for identity,
knowledge timing, permission use, detached source binding and professional acceptance
boundaries. The package retains its native schema; no universal adapter is implied.
