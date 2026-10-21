---
name: market-landscape-researcher
description: "Organize supplied industry findings by requested dimensions, retain source provenance and compute concentration only when cited comparable shares are supplied. Use for qualitative or quantitative landscape research; missing or ineligible evidence remains partial, not a recommendation."
license: MIT
compatibility: Amazon Quick Desktop; requires approved-source-retrieval (filings/research/deal data), document-intelligence, entity-resolution, CRM/data-room, and controlled-content MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Investment Research"
  aws-fsi-skill-type: "Guidance or domain-expertise skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Domain workflow"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 2 - analytical production"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "existing-updated"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (MNPI / client-confidential)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Investment Research"
  aws-fsi-primary-user: "Banking / research analyst or strategist"
  aws-fsi-version: "0.3.0"
  aws-fsi-recertification-date: "2027-10-20"
---

# market-landscape-researcher

Synthesize supplied findings into a purpose-scoped industry map. No live retrieval, market-definition validation or competition-law opinion is implemented.

Use this package for its supplied-input job. Requests for missing source retrieval, professional conclusions, live actions or distribution require the separately provisioned owner and access. Read [native contract](references/phase1-contract.md) before preparing inputs and [controls](references/controls.md) before using results.

## Native operation

1. Establish issuer/document/market identity, permitted purpose and audience. Retain the original supplied JSON separately.
2. Run `python3 -B scripts/validate_input.py INPUT.json`. Missing evidence is never filled from fixtures.
3. Run `python3 -B scripts/calculate_or_transform.py INPUT.json` to produce native JSON.
4. Run `python3 -B scripts/validate_output.py OUTPUT.json --input INPUT.json`. No output-only validation, embedded source snapshot or extra narrative is supported. `--selftest` uses the retained example input and refreshed golden result.
5. Review partial/not-evaluable fields and unresolved items before preparing an audience-specific narrative separately. A reconstructed result does not authenticate sources, grant access or establish professional acceptance.

## Boundaries and handoffs

Profile facts and business-model assessment establish issuer context. market-sizing-builder owns market estimation. Qualitative work does not require numeric shares. Market definition, comparable share bases, source authority, interpretation and permitted use require analyst review.

Read [handoffs](references/handoffs.md), [sources](references/source-map.md) and [domain method](references/domain-rules.md). Offline JSON operations are implemented; live connectors, verified entitlements, institutional policies and professional acceptance are deployment dependencies. Package hashes establish reproducibility only.

## Shared Phase 1 evidence standard

Read [the evidence and control standard](references/evidence-standard.md) for identity,
knowledge timing, permission use, detached source binding and professional acceptance
boundaries. The package retains its native schema; no universal adapter is implied.

## Phase 2 native analysis

For `schema_version: ir-phase2/1.0`, read [the analytical intake and method](references/phase2-contract.md). This expands the method with source eligibility, basis and timing controls through the supplied-evidence analysis contract. Legacy Phase 1 inputs retain their existing interface. Both modes require the separately retained original for full output reconstruction. A reviewed adapter validates producer and receiver; a supplied status label is not an approval.
