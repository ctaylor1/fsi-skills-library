---
name: compliance-remediation-evidence-reviewer
description: >-
  Assess remediation evidence against the original accepted finding, closure criteria, retest failures, operating coverage and sustained-operation window. Draft criterion-level closure evidence gaps and owner review recommendations without closing findings or converting fresh design documents into proof of effectiveness.
license: MIT
compatibility: Offline Python 3.10+ standard-library helpers and supplied evidence; no live connector is bundled.
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
  aws-fsi-data-classification: "Restricted; source-specific confidentiality and audience limits"
  aws-fsi-jurisdictions: "Supplied reviewed jurisdiction and institution profile; no universal legal default"
  aws-fsi-owner: "Finding Owner / Authorized Closure Reviewer"
  aws-fsi-primary-user: "Mandated compliance analyst and accountable professional reviewer"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-10-03"
---

# Compliance Remediation Evidence Reviewer

Assess remediation evidence against the original accepted finding, closure criteria, retest failures, operating coverage and sustained-operation window. Draft criterion-level closure evidence gaps and owner review recommendations without closing findings or converting fresh design documents into proof of effectiveness.

Read [domain rules](references/domain-rules.md) and [input schema](references/input-schema.md)
for the native method. Read [source map](references/source-map.md), [controls](references/controls.md)
and [handoffs](references/handoffs.md) before using evidence or transferring a draft.

## Method

Bind every criterion and retest to the original finding/version and affected scope. Compare evidence with acceptance criteria and the required operation window. Distinguish designed, implemented, retested and sustained states; a policy rewrite is design evidence only. Count known failures, unknown/untested records and coverage gaps separately. Supplied approver identity/acceptance is retained as unverified evidence, never authenticated authority. Withhold a closure-evidence recommendation when original acceptance, criterion coverage, operating evidence, retest or authority is missing or contradicted.

Separate intake/triage from substantive review: route malformed requests to intake correction;
retain unsupported legal profiles and substantive unknowns in the draft. Require a durable
case ID, review date/cutoff, authorized purpose/audience and source-specific classification.
Supplied source facts, profile assertions and authority records remain unverified. An evidence
registry alone never supports a claim; map each consequential field to an exact source fact.

## Deliverable and verification

Original-finding linkage, criterion-by-criterion design/implementation/operating evidence, retest failures and unknowns, sustained-operation/coverage gaps and closure-review prerequisites. Use the [output template](assets/output-template.md) for human narrative;
keep it separate from the immutable native result. Source-bound native calculations have no
professional adjudication or action capability.

```sh
python3 -B scripts/validate_input.py INPUT.json
python3 -B scripts/calculate_or_transform.py INPUT.json > OUTPUT.json
python3 -B scripts/validate_output.py OUTPUT.json --input INPUT.json
python3 -B scripts/test_phase2.py
python3 -B scripts/run_evals.py
```

Retain the original input separately and require exact detached-output reconstruction before
presenting a native result. Invalid structural input stops calculation; null, conflicted,
restricted, stale or unsupported facts withhold dependent conclusions. Unknown is never zero,
pass, innocent, approved or closed. Added narrative or edited native fields fail validation.

## Professional boundary

The accountable owner is **Finding Owner / Authorized Closure Reviewer**. This is internal read-only decision support.
Legal interpretation, authentication, human acceptance, regulated decisions, privilege,
HR action, approval, filing, closure and external delivery stay with authorized professionals.
No token or asserted user approval enables live execution. No system-of-record mutation,
access grant, list change, witness contact, payment, publication or customer communication is
implemented. Synthetic checks prove bounded behavior only; source truth, professional
acceptance and production readiness remain unestablished.

Shared [foundation contract](references/foundation-contract.md), [evidence contract](references/evidence-contract.md)
and [source governance](references/source-governance.md) govern provenance, scope, detached validation and handoff limits.
