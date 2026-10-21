---
name: policy-procedure-gap-analyzer
description: >-
  Compare supplied applicable requirements with documented policies and control design; identify coverage, parameter, evidence-pointer, version and review gaps. Supports current design and future readiness, not operating-effectiveness testing, compliance certification or policy approval.
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
  aws-fsi-data-classification: "Confidential policy and control design evidence; apply source-specific restrictions"
  aws-fsi-jurisdictions: "Supplied institution/jurisdiction profile; no default legal applicability or bundled current-law pack"
  aws-fsi-owner: "Regulatory Compliance Advisory / Policy Owners"
  aws-fsi-primary-user: "Compliance advisory / policy owner / audit"
  aws-fsi-version: "0.1.1"
  aws-fsi-recertification-date: "2027-07-17"
---

# Policy Procedure Gap Analyzer

Use for requirement-to-policy/control design analysis. Compliance advisory and policy owners review the substantive gaps. Auditors may consume the draft but this workflow does not provide independent assurance or certify controls operated.

Read [domain rules](references/domain-rules.md) for the bounded method and schema,
[source map](references/source-map.md) for evidence requirements, and
[controls](references/controls.md) before preparing a result.

## Workflow

- Explicit applicability is required for a clean result. Unknown applicability stays unevaluable; a supplied false value is informational and retains its review responsibility.
- Future-effective requirements are assessed for readiness; findings carry `future_readiness` instead of being discarded. Present findings carry `current_design`. Neither is an adjudicated regulatory breach.
- The three supported comparator pairs are retention minimum years versus retention years, maximum reporting threshold USD versus reporting threshold USD, and maximum training interval months versus training interval months. They are supplied requirement parameters, not universal legal thresholds.
- Missing or unsupported control parameters remain unevaluable. Such requirements cannot appear in `clean_requirements`. Missing/future control-review dates and other control findings also prevent a clean label for mapped requirements.
- An evidence pointer records where an artifact is said to exist. It never proves source truth, design sufficiency beyond these checks, operating effectiveness, sampling adequacy or control execution. `operating_effectiveness_status` is always `not_assessed`.

## Input, output and verification

Supplied framework/jurisdiction, assessment date/config version, requirements with citations/criticality/applicability/effective dates, policy-control mappings, review dates and optional parameter objects. Numeric parameters must be finite. `clean_requirements` means no detected design issue within supported checks, not compliance.

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

Regulatory changes come from `regulatory-change-impact-analyzer`; approved drafting requirements go to enterprise `policy-document-assistant`. RCSA remains first-line assessment. Operating control testing, independent assurance and issue closure need separately authorized owners/workflows; do not describe this package as continuous monitoring.

Only the documented comparator types and document/mapping checks are implemented. No operational samples are evaluated; no wording is approved, finding closed, report filed or policy edited.

Read [handoffs](references/handoffs.md) before transferring evidence. Apply source-specific
confidentiality, minimization and audience controls; SAR restrictions attach only when the
actual source/use warrants them, not to every generic compliance artifact.

Shared [evidence contract](references/evidence-contract.md) and [source governance](references/source-governance.md) define cross-workflow provenance and authority boundaries.
