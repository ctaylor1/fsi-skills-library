---
name: compliance-financial-crime-risk-assessor
description: >-
  Assess supplied institution compliance and financial-crime risk dimensions using explicit accepted methods, separating inherent exposure, control evidence and residual risk. Use for scoped institutional risk assessments; no universal scoring weights, legal taxonomy or favorable missing-evidence defaults are bundled.
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
  aws-fsi-owner: "Financial Crime Risk / Compliance Risk Owner"
  aws-fsi-primary-user: "Compliance professional / accountable institutional reviewer"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-10-03"
---

# Compliance Financial Crime Risk Assessor

Use when the institution needs a scoped financial-crime/compliance risk assessment under its accepted method. Produce a **Dimension-level inherent/control/residual assessment with method acceptance, evidence gaps, sensitivity and professional review questions**. Interpret primary text and institution artifacts before constructing native input; the helper consumes reviewed extracted facts and supplies bounded checks. It does not independently perform professional review.

Read [domain rules and input schema](references/domain-rules.md), [source map](references/source-map.md) and [controls](references/controls.md). For another owner’s job, read [handoffs](references/handoffs.md).

## Professional workflow

- Establish institution/entity/activity/population scope, period and material dimensions from the accepted risk taxonomy. Preserve ML, TF, PF, sanctions and other dimensions separately where the institution method requires them.
- Obtain the actual method, weight/scale/boundary definitions, acceptance evidence, approver and version. Describe supplied policy separately from primary-source facts; a convenient formula is not a regulator-prescribed model.
- Assess exposure and risk drivers from source-backed facts, keeping inherent risk separate from control design, implementation, testing and operating evidence.
- Calculate a residual indicator only when the supplied method is supported, accepted, complete, each required dimension/weight exists, and operating control evidence supports the supplied control factor. Partial input cannot produce a lower residual conclusion.
- Explain aggregation, sensitivity and missingness. Weighted averages can mask high dimensions; retain every dimension and do not create a universal low/medium/high cutoff.
- Human risk owners adjudicate risk, appetite and action. Enterprise-risk aggregation and model validation remain with their specialist owners.

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
