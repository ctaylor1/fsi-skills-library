---
name: regulatory-obligation-control-mapper
description: >-
  Map supplied regulatory provisions to policies, processes, controls, systems, data, evidence and accountable owners, including orphan and unresolved coverage relationships. Use for baseline obligation inventory and control traceability; mapping alone does not establish compliance or effectiveness.
license: MIT
compatibility: Offline Python 3.10+ standard-library helpers and supplied evidence; enterprise data and live adapters are not bundled.
metadata:
  aws-fsi-category: "Compliance & Financial Crime"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 3 — regulated casework"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Confidential; apply source-specific restrictions"
  aws-fsi-jurisdictions: "Supplied entity/activity/jurisdiction profile; no default legal profile"
  aws-fsi-owner: "Regulatory Compliance / Control Framework Owner"
  aws-fsi-primary-user: "Compliance professional / accountable institutional reviewer"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-10-03"
---

# Regulatory Obligation Control Mapper

Use when a baseline provision inventory must be traced to the institution operating model or orphan controls/obligations must be found. Produce a **Provision-to-operating-model matrix, coverage denominators, orphan register and unresolved linkage questions**. Interpret primary text and institution artifacts before constructing native input; the helper consumes reviewed extracted facts and supplies bounded checks. It does not independently perform professional review.

Read [domain rules and input schema](references/domain-rules.md), [source map](references/source-map.md) and [controls](references/controls.md). For another owner’s job, read [handoffs](references/handoffs.md).

## Professional workflow

- Extract provisions with exact primary-source locators, version, authority/lifecycle and date distinctions. Legal/compliance supplies applicability; contractual clauses belong with the contract specialist.
- Inventory policies, processes, controls, systems, data elements, evidence artifacts and accountable owners with stable IDs, scope and source-backed existence/status. Names alone do not demonstrate implementation.
- Create explicit provision-to-component relationships and preserve relationship evidence, owner, scope and any reviewed exception. Do not infer links from similar wording or silently drop a difficult dimension.
- Trace each applicable or unresolved provision across every required operating-model dimension. Separate supported coverage, unknown coverage, incomplete/absent evidence and approved exceptions.
- Report orphan provisions and orphan inventory items, cross-scope links and unresolved applicability in both directions. Denominators come from the supplied inventory and applicability scope; a ratio is not assurance.
- Preserve operating-performance and independent-testing conclusions for their own mandates. Route policy design gaps or remediations with the exact unmapped provision and supporting evidence.

## Native evidence and verification

Use durable `request_id` and `object_id`, the assessment `as_of`, source registry, exact fact-to-source field mappings, purpose, audience and classification from the [common foundation contract](references/foundation-contract.md). A declared source status is unverified supplied evidence; missing, unknown, conflicting or stale facts remain unresolved. Retain actual/event dates separately from effective and compliance dates.

```sh
python3 -B scripts/validate_input.py INPUT.json
python3 -B scripts/calculate_or_transform.py INPUT.json > OUTPUT.json
python3 -B scripts/validate_output.py OUTPUT.json --input INPUT.json
python3 -B scripts/test_phase2.py
```

Retain original input separately. All calculator paths validate before calculating, and native results require exact detached reconstruction. Keep human interpretation and any workflow envelope separate from the native result. Use [output template](assets/output-template.md) for the professional deliverable; do not treat native arithmetic as an approved institutional judgment.

The shipped method is offline supplied-evidence support. Source authentication, legal completeness, institutional acceptance, professional independence, representative population access and operational authorization remain deployment dependencies. No approvals, launches, filings, changes to permissions or external notifications are performed.
