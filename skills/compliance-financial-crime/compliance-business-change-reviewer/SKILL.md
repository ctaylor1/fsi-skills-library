---
name: compliance-business-change-reviewer
description: >-
  Review exact business-change scope, compliance dependencies, release criteria and open blockers using supplied perimeter, control, data, training and specialist evidence. Use before a new product, entity, market or operating-model release; produces review support without granting launch approval.
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
  aws-fsi-owner: "Compliance Advisory / Business Change Owner"
  aws-fsi-primary-user: "Compliance professional / accountable institutional reviewer"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-10-03"
---

# Compliance Business Change Reviewer

Use when a new product, market, acquisition, entity, distribution arrangement or operating-model change needs compliance review before release. Produce a **Scoped change dependency review with release-by-release prerequisites, blockers, accepted exceptions and owner questions**. Interpret primary text and institution artifacts before constructing native input; the helper consumes reviewed extracted facts and supplies bounded checks. It does not independently perform professional review.

Read [domain rules and input schema](references/domain-rules.md), [source map](references/source-map.md) and [controls](references/controls.md). For another owner’s job, read [handoffs](references/handoffs.md).

## Professional workflow

- Define the exact proposed change and each release scope: entities, activities, products, markets, channels, customers and dates. Compare baseline and target scope; do not reuse a predecessor review for a larger launch.
- Identify applicability/permissions, policy/process/control, system/data, resourcing/training and specialist dependencies. Use the institution release criteria; no generic completeness checklist grants approval.
- Bind each dependency status and specialist result to the same change/release scope and version. A broad success label or another team’s completed review does not prove that this release is covered.
- Evaluate predecessor relationships and release prerequisites, including unresolved blockers and explicitly scoped exception evidence. A waiver is a supplied reviewed exception for one dependency, not a transferable legal permission.
- Preserve unknown/partial/blocked statuses and future-effective obligations as preparation dependencies. Actual operation/start, legal effective and compliance dates remain distinct.
- Produce the review register and human launch decision questions. Technology/model/privacy/payments/sector owners retain their specialized methods and execution controls.

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
