---
name: insurance-delegated-authority-reviewer
description: "Review a proposed insurance activity against an executed, versioned delegation and supplied utilization and bordereaux evidence. Use to check parties, actions, product/jurisdiction scope, dates, financial limits, reporting breaks and exceptions. Produces a review matrix; never grants authority, binds, settles, approves an exception or updates a ledger."
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
  aws-fsi-primary-user: "MGA oversight / delegated authority control reviewer"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-09-18"
---

# Delegated Authority and Bordereaux Review

Produce a source-linked draft for the accountable mga oversight / delegated authority control reviewer. For example: “Review whether the MGA’s proposed property activity falls within this agreement and identify aggregate-capacity or overdue bordereaux exceptions.”

## Workflow

1. Identify insurer, delegate, activity, transaction, jurisdiction, insurance line and amount basis. Obtain the executed agreement and applicable amendments; a producer license or earlier approval does not create contractual delegation.
2. Extract explicit scope, effective period, permitted actions and monetary limits into the reviewed input. Preserve prohibitions, referral thresholds, restrictions, revocation/suspension notices and exception schedules for the human reviewer. Do not assume that underwriting, claims and subdelegation rights travel together.
3. Check party, action, product and jurisdiction matches. Evaluate the transaction date against the exact agreement version. Separate absent evidence from a known scope or date exception.
4. Check currency and amount definition before comparing a per-risk limit. For aggregate capacity, require a complete, same-date ledger for that agreement version and basis, explicitly excluding the proposed transaction. Missing utilization never means zero; a previously counted transaction is not added again.
5. Reconcile the supplied reporting schedule and bordereaux against the expected totals on the same basis. Preserve overdue/late receipt and signed differences. Missing reports, incomplete extracts and unknown financial bases remain gaps.
6. Draft the exception and oversight packet with references to the relevant clauses, amendments, ledger and reports. The insurer's accountable reviewer resolves ambiguities and grants any approval through separate controls.

## Resources and deterministic work

Read [domain rules](references/domain-rules.md) for method limits, [source map](references/source-map.md) before asserting applicability, and [schema](references/schema.md) when normalizing evidence. Read [controls](references/controls.md) before preparing regulated decision support and [handoffs](references/handoffs.md) when the request crosses ownership.

Validate normalized input with `python scripts/validate_input.py input.json`; produce the immutable review record with `python scripts/calculate_or_transform.py input.json`; check that record with `python scripts/validate_output.py output.json`. A command exit of zero means the structure/evaluation ran, not that the case cleared. Inspect status, findings, completeness and evaluability. Run [regressions](scripts/test_workflow.py) for changed methods.

Use [the draft template](assets/output-template.md) to prepare the human review memo and [the worked synthetic input](evals/files/normal.json) for the exact native schema. Keep source_document attached; do not edit generated evidence statuses to make the packet appear ready. The bundled [insurance contract](references/insurance-contract.md) explains content binding and portable handoffs.

## Failure handling and acceptance

Missing business evidence should produce a useful gap packet; malformed inputs must be corrected. A source reference or evidence-present state does not establish authenticity, complete discovery, legal compliance or professional acceptance. Preserve disputed and adverse facts. Mandatory human adjudication remains distinct from software completeness. This release has offline regression coverage; live-source, professional and deployment acceptance are separate gates.

See [native workflow foundation](references/insurance-foundation.md) for source-bound context mappings, inherited uncertainty and output validation.
