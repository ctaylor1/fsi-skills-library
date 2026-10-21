---
name: sustainability-mandate-reviewer
description: "Review a supplied sustainability mandate against source-linked portfolio metrics, exclusions, data coverage, vintages and estimates. Use for an internal mandate evidence review; no generic ESG score, sustainability label or compliance certification."
license: MIT
compatibility: Python 3.10+ standard-library offline supplied JSON; source authentication and institutional/legal acceptance remain external.
metadata:
  aws-fsi-category: "Asset Management"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 8 - asset management specialized extensions"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (MNPI / client-confidential)"
  aws-fsi-jurisdictions: "Explicit supplied reviewed mandate and legal scope; no universal jurisdiction pack"
  aws-fsi-owner: "Asset Management investment and operations"
  aws-fsi-primary-user: "Sustainability investment and control reviewer"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-10-04"
---

# Sustainability mandate review

Use this skill to test a supplied investment mandate against an actual holdings snapshot and documented sustainability metrics. Establish the mandate version, accountable investment/control owner and review date before calculating. A product's name, vendor rating or investment theme does not establish its mandate or regulatory classification.

Read the [schema](references/schema.md) and [method](references/domain-rules.md). Reconcile all holding market values to the supplied portfolio denominator. Declare the metric-eligible population and every excluded holding's basis. Keep units, definition versions, fiscal vintages and reported/estimated flags exact; a metric with the wrong vintage is unavailable for this calculation.

Review coverage before interpreting aggregate values. A missing eligible metric is not zero, and a covered-only mean is not a full-portfolio result. Retain known exclusion breaches even when another holding is unknown. Identify the metric owner who can resolve each unavailable value or mandate term.

Run `python3 -B scripts/validate_input.py REQUEST.json`, then `python3 -B scripts/calculate_or_transform.py REQUEST.json`. Retain the original separately and validate the saved result with `python3 -B scripts/validate_output.py OUTPUT.json --input REQUEST.json`. Use the [review template](assets/output-template.md) to distinguish facts, assumptions, coverage and unresolved decisions.

Apply [controls](references/controls.md) and preserve [source provenance](references/source-map.md). Use [handoffs](references/handoffs.md) for data, disclosure and jurisdiction questions. The native method supplies exact long-only weighted arithmetic and supplied exclusion checks. It does not estimate missing emissions, build financed-emissions inventories, infer derivative/short exposures, apply a universal taxonomy or award a sustainability label. No investment, divestment, disclosure or certification action is performed.
