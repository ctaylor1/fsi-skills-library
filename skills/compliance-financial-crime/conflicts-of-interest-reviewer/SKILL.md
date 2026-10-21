---
name: conflicts-of-interest-reviewer
description: >-
  Review supplied interest, outside-activity, gift, relationship, personal-trading and related-party disclosures for documented conflict indicators and control gaps. Preserve unknown facts and route for human ethics/compliance review; no clearance, waiver or mitigation-effectiveness determination.
license: MIT
compatibility: Offline Python 3.10+ standard-library helpers and supplied evidence; no live connector or operational adapter is bundled.
metadata:
  aws-fsi-category: "Compliance & Financial Crime"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "existing-updated"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Confidential employee and conflicts evidence; need-to-know access"
  aws-fsi-jurisdictions: "Supplied institution/jurisdiction profile; no default legal applicability or bundled current-law pack"
  aws-fsi-owner: "Employee Conduct / Conflicts and Ethics Compliance"
  aws-fsi-primary-user: "Compliance / legal / business supervisor"
  aws-fsi-version: "0.1.1"
  aws-fsi-recertification-date: "2027-07-17"
---

# Conflicts of Interest Reviewer

Use for a disclosed conflict matter and its evidence. Employee-conduct compliance owns review; legal, supervisors and designated committees retain authority to decide conditions, exceptions and conflicts. No investigation finding or disciplinary decision is made.

Read [domain rules](references/domain-rules.md) for the bounded method and schema,
[source map](references/source-map.md) for evidence requirements, and
[controls](references/controls.md) before preparing a result.

## Workflow

- Numeric thresholds come from an explicit supplied institution policy/configuration; they are not statutory thresholds. Missing policy evidence or necessary magnitude/MNPI facts makes the relevant indicator `Unknown`, never a zero-value or non-MNPI assumption.
- Gifts require supplied aggregate completeness before a below-threshold indicator. This calculator does not build a cross-record annual gift ledger or decide legal exclusions. Review aggregation, direction, recipient and applicable legal rules separately.
- Documentary checks assess dated disclosures, scoped sourced controls and supplied approvals. An approval must state decision, item scope, source, date and expiry covering the assessment date. Future/stale disclosure records and expired/out-of-scope approval claims do not satisfy the checklist.
- Document presence earns no mitigation credit. Each `residual_risk` and `matter_residual_risk` is `not_assessed`; the separate inherent indicator guides review. Source authenticity and control effectiveness remain unverified even when the documentary checklist is complete.
- Unknown facts or missing required records route to a conflicts/ethics reviewer. A below supplied threshold result is not an exemption, no-conflict finding or clearance.

## Input, output and verification

Matter/as-of/config version, subject, cited conflict items, magnitude/MNPI facts, disclosures, scoped controls, approval claims and institution policy configuration. `aggregation_complete` is a supplied evidence assertion. Numeric fields are finite and nonnegative.

The script returns an immutable native draft with `input_hash` and `source_truth=unverified`.
Retain the original input separately; raw source embedding and added narrative fields are
rejected. Hashing proves repeatability against supplied input, not authenticity or approval.
Human narrative, legal reasoning and any workflow envelope stay separate and need their own
source, audience and professional review.

```sh
python -B scripts/validate_input.py INPUT.json
python -B scripts/calculate_or_transform.py INPUT.json
python -B scripts/validate_output.py OUTPUT.json --input INPUT.json
python -B scripts/test_phase1.py
```

Do not present a native result until detached-input reconstruction passes. Invalid structural
inputs stop calculation; substantive unknowns stay visible. Software tests and synthetic
fixtures establish bounded behavior only, not legal correctness or production acceptance.

## Boundaries and handoffs

`employee-trading-preclearance-reviewer` handles proposed employee trades; `market-surveillance-alert-investigator` handles market-activity evidence; Wealth `investment-recommendation-evidence-reviewer` owns recommendation files. Policy gaps, third-party bribery concerns and misconduct allegations need their own scoped owners; this checklist does not replace them.

Default control checklists are illustrative triage prompts, not jurisdiction-specific law or a verified institution approval matrix. No approvals are authenticated, no mitigation effectiveness assessed, and no matter is cleared, waived, closed, filed or entered into a register.

Read [handoffs](references/handoffs.md) before transferring evidence. Apply source-specific
confidentiality, minimization and audience controls; SAR restrictions attach only when the
actual source/use warrants them, not to every generic compliance artifact.

Shared [evidence contract](references/evidence-contract.md) and [source governance](references/source-governance.md) define cross-workflow provenance and authority boundaries.
