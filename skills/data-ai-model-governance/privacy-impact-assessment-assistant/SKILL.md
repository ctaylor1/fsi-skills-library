---
name: privacy-impact-assessment-assistant
description: >-
  Assemble a supplied PIA/DPIA evidence draft with explicit jurisdiction and legal-applicability context, claim-level sources, open gaps and an inherent-risk indicator. Supports controller/privacy/legal review; does not infer residual risk, approve processing or decide Article 36 consultation.
license: MIT
compatibility: Offline Python 3.10+ standard-library helpers and supplied evidence; no live connector or operational adapter is bundled.
metadata:
  aws-fsi-category: "Data, AI & Model Governance"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Draft & package"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "existing-updated"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Restricted privacy assessment and personal-data processing evidence"
  aws-fsi-jurisdictions: "Supplied institution/jurisdiction profile; no default legal applicability or bundled current-law pack"
  aws-fsi-owner: "Privacy Office / Accountable Controller; DPO advisory"
  aws-fsi-primary-user: "Privacy officer / product risk / legal"
  aws-fsi-version: "0.1.1"
  aws-fsi-recertification-date: "2027-07-17"
---

# Privacy Impact Assessment Assistant

Use for a privacy impact assessment of a supplied processing activity. The accountable controller owns processing decisions; authorized privacy/legal owners review legal questions; the DPO advises and monitors independently. The package resides in Data, AI & Model Governance. Compliance and financial-crime workflows consume its scoped privacy findings.

Read [domain rules](references/domain-rules.md) for the bounded method and schema,
[source map](references/source-map.md) for evidence requirements, and
[controls](references/controls.md) before preparing a result.

## Workflow

- Supply the jurisdiction and reviewed legal profile with rationale and sources. US context does not automatically establish GDPR applicability; sensitivity under institution policy does not automatically make data an Article 9 category.
- Each of the eight evidence sections carries claim IDs/text/citation references. Each citation resolves to a supplied registry locator, version and excerpt. Section-level citation presence cannot compensate for unsupported individual claims. Excerpts still require substantive human review.
- Open section gaps prevent ready-for-adjudication. Missing jurisdiction/profile or any required risk factor also yields `needs-information`; absent factors never produce Low. Explicit adverse legal indicators yield `blocked` pending counsel review, not an illegality determination.
- The numeric method is an inherent-risk triage indicator only. `residual_risk_band` remains `not_assessed` because the calculator does not test mitigation effectiveness. Complete inputs may produce Low/Medium/High; those labels are not legal DPIA thresholds.
- `prior_consultation_indicated` remains null: no Article 36 decision follows from the score. Qualified reviewers assess applicability, remaining risk, measures and any consultation obligations in context.
- Supplied approval records are labelled `supplied-unverified`, never authenticated/obtained by this package. Ready-for-adjudication means structured evidence completeness for human review, not approval or substantive sufficiency.

## Input, output and verification

Processing context, config/template identifiers, assessment ID, jurisdiction/legal profile, all explicit risk factors, evidence sections with individually cited claims, source registry and institutional reviewer/approval roles. Missing substantive evidence remains a visible gap.

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

`ai-risk-assessment-builder` handles AI-specific risk; `data-lineage-documenter` handles data flows; `third-party-risk-assessor` handles processor risk. Regulatory-change and policy-gap workflows consume scoped findings. CFC overlays address AML retention, SAR restrictions and lawful sharing without redefining generic privacy ownership.

No jurisdictional law pack, legal-basis decision, mitigation-effectiveness validation, processing approval, authenticated sign-off, consultation submission, filing or system change is implemented. Supplied sources are unverified; standard template coverage is not legal compliance.

Read [handoffs](references/handoffs.md) before transferring evidence. Apply source-specific
confidentiality, minimization and audience controls; SAR restrictions attach only when the
actual source/use warrants them, not to every generic compliance artifact.

Shared [evidence contract](references/evidence-contract.md) and [source governance](references/source-governance.md) define cross-workflow provenance and authority boundaries.
