---
name: regulatory-applicability-reviewer
description: >-
  Review cross-entity regulatory perimeter and permissions using supplied authority versions, entity/activity/nexus facts, thresholds and exceptions. Use to assess which supplied rules may apply; retains unknown or contested interpretations for legal review.
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
  aws-fsi-owner: "Regulatory Compliance / Legal Advisory"
  aws-fsi-primary-user: "Compliance professional / accountable institutional reviewer"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-10-03"
---

# Regulatory Applicability Reviewer

Use when a rule, permission or regulatory perimeter must be evaluated across entities, activities or cross-border nexus. Produce a **Rule-by-entity applicability matrix with criterion-level evidence, permissions, open interpretations and legal-review questions**. Interpret primary text and institution artifacts before constructing native input; the helper consumes reviewed extracted facts and supplies bounded checks. It does not independently perform professional review.

Read [domain rules and input schema](references/domain-rules.md), [source map](references/source-map.md) and [controls](references/controls.md). For another owner’s job, read [handoffs](references/handoffs.md).

## Professional workflow

- Capture each authority, version, source, lifecycle status and publication/effective/compliance dates independently. Obtain a legally reviewed rule profile; no jurisdiction or institution defaults are bundled.
- Identify the actual entity, activity, product, customer location, establishment/solicitation nexus and permissions. Absence of a keyword match does not prove that an activity falls outside a perimeter.
- Translate reviewed rule conditions into explicit supplied comparisons. Identify whether the required condition is all-of or any-of, and retain missing/conflicting facts. Record exemptions separately and require the supplied exemption method.
- Compare each criterion to its evidence and show the intermediate result for each rule/entity pair. A false conjunct can support a perimeter mismatch only for a complete, supported rule profile; an unsupported operator/profile remains unsupported.
- Assess separately the permission inventory against permissions specified by the supplied rule. A rule not currently effective can still produce preparation questions without a present-breach claim.
- Legal owns contested interpretation, authorization and final applicability. Route implementation impact and sector-specific meaning after the scoped applicability evidence is reviewed.

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
