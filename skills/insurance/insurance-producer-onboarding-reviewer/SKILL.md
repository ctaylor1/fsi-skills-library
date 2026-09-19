---
name: insurance-producer-onboarding-reviewer
description: "Reconcile individual and business-entity producer identity, licensing, appointment, jurisdiction and line-of-authority evidence against a reviewed onboarding profile. Use for producer onboarding, renewal or credential exceptions. Produces a dated evidence matrix and unresolved exceptions; does not appoint a producer, authorize carrier representation, determine legal validity or activate access."
license: MIT
compatibility: Python 3.10+; offline structured evidence. No bundled production connectors or external execution.
metadata:
  aws-fsi-category: "Insurance"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Insurance Phase 2"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "Reviewed target-specific jurisdiction/product profiles required; synthetic fixtures establish no local law"
  aws-fsi-owner: "Insurance distribution and sales supervision"
  aws-fsi-primary-user: "Producer licensing / distribution compliance reviewer"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-09-18"
---

# Producer Onboarding Evidence Review

Produce a source-linked draft for the accountable producer licensing / distribution compliance reviewer. For example: “Review these individual and agency licensing exports for the intended carrier and property line; list what prevents an onboarding reviewer from deciding.”

## Workflow

1. Establish the individual, business entity, insurer, intended activity, jurisdiction and requested lines. Separate each legal entity and role; a shared trade name is not proof that two records identify the same licensee.
2. Obtain current regulator or authorized licensing-feed evidence, insurer appointment evidence, and the reviewed jurisdiction/activity requirements. Populate one requirement for every intended entity/jurisdiction/line/carrier scope. Record why an appointment is required, not required, or unresolved; never assume a nationwide appointment rule.
3. Reconcile legal names and scope before considering active status. Preserve duplicate or contradictory records and retain all source references. An absent license is unknown, while an evidenced expired or suspended license is an observed exception.
4. Apply the configured evidence freshness interval and effective/expiry dates as of the requested review date. Missing expiry requires an explicit sourced non-expiring status. The interval is institution configuration, not a statutory default.
5. Draft follow-up requests for missing identity, responsible-producer/business-entity requirements, line mapping, appointments, restrictions, training and carrier contracts as applicable. The scripted matrix covers only supplied requirements; human review must assess whether that scope is complete.
6. Package the evidence for the licensing owner. Keep credential readiness distinct from insurer contract authority, system access activation and actual onboarding approval.

## Resources and deterministic work

Read [domain rules](references/domain-rules.md) for method limits, [source map](references/source-map.md) before asserting applicability, and [schema](references/schema.md) when normalizing evidence. Read [controls](references/controls.md) before preparing regulated decision support and [handoffs](references/handoffs.md) when the request crosses ownership.

Validate normalized input with `python scripts/validate_input.py input.json`; produce the immutable review record with `python scripts/calculate_or_transform.py input.json`; check that record with `python scripts/validate_output.py output.json`. A command exit of zero means the structure/evaluation ran, not that the case cleared. Inspect status, findings, completeness and evaluability. Run [regressions](scripts/test_workflow.py) for changed methods.

Use [the draft template](assets/output-template.md) to prepare the human review memo and [the worked synthetic input](evals/files/normal.json) for the exact native schema. Keep source_document attached; do not edit generated evidence statuses to make the packet appear ready. The bundled [insurance contract](references/insurance-contract.md) explains content binding and portable handoffs.

## Failure handling and acceptance

Missing business evidence should produce a useful gap packet; malformed inputs must be corrected. A source reference or evidence-present state does not establish authenticity, complete discovery, legal compliance or professional acceptance. Preserve disputed and adverse facts. Mandatory human adjudication remains distinct from software completeness. This release has offline regression coverage; live-source, professional and deployment acceptance are separate gates.

See [native workflow foundation](references/insurance-foundation.md) for source-bound context mappings, inherited uncertainty and output validation.
