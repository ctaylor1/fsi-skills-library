---
name: compliance-program-effectiveness-reviewer
description: >-
  Review supplied program coverage, outcomes, quality and resourcing metrics with exact denominators, evidence limitations and mandate boundaries. Use for management or second-line effectiveness reviews; lower alerts or faster closure alone do not demonstrate effectiveness or independent assurance.
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
  aws-fsi-owner: "Compliance Oversight / Program Effectiveness Owner"
  aws-fsi-primary-user: "Compliance professional / accountable institutional reviewer"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-10-03"
---

# Compliance Program Effectiveness Reviewer

Use when management/oversight needs an evidence-based program effectiveness review for a specified population and period. Produce a **Coverage, outcome, quality and resources readout with denominators, comparability, assurance mandate and unresolved evidence questions**. Interpret primary text and institution artifacts before constructing native input; the helper consumes reviewed extracted facts and supplies bounded checks. It does not independently perform professional review.

Read [domain rules and input schema](references/domain-rules.md), [source map](references/source-map.md) and [controls](references/controls.md). For another owner’s job, read [handoffs](references/handoffs.md).

## Professional workflow

- Establish period, population, controls/program perimeter, review mandate and accountable audience. Distinguish management self-assessment, operational QA, second-line monitoring, independent testing and audit with actual mandate evidence.
- Build the full inventory of required metrics and outcomes under the supplied measurement plan. Keep coverage, detection/prevention outcomes, quality, timeliness and resources separately interpretable.
- Validate every numerator/denominator against matching scope, period and lineage. Sampling, selection bias, missing labels, threshold changes and data-access gaps limit what the result can establish.
- Compare periods only with supported comparable populations, definitions and operating conditions. Alert reduction or faster closure can reflect suppression, under-detection or process changes; do not label these as success without outcome/quality evidence.
- Describe adverse outcomes, control failures, issue recurrence, customer impact and resourcing constraints alongside operational activity. Ground conclusions in exact evidence; no single universal effectiveness score is included.
- Produce review conclusions and practical follow-up questions; independent assurance and certification require the separately evidenced mandate and authorized reviewer.

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
