---
name: regulatory-change-impact-analyzer
description: >-
  Assess supplied regulatory changes, lifecycle states, applicability evidence and implementation mappings for human regulatory-compliance review. Produces an offline impact assessment; does not authenticate primary sources, decide legal applicability, monitor feeds or close changes.
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
  aws-fsi-data-classification: "Confidential regulatory-change analysis; apply source-specific restrictions"
  aws-fsi-jurisdictions: "Supplied institution/jurisdiction profile; no default legal applicability or bundled current-law pack"
  aws-fsi-owner: "Regulatory Compliance / Regulatory Change Management"
  aws-fsi-primary-user: "Regulatory-change analyst / compliance advisory"
  aws-fsi-version: "0.1.1"
  aws-fsi-recertification-date: "2027-07-17"
---

# Regulatory Change Impact Analyzer

Use for a supplied law, rule, guidance or standards change and its institution impact. Extract and verify obligations against primary text before constructing the input; the script consumes already extracted obligations. Analysts own the evidence pack; legal/compliance owners decide applicability and implementation closure.

Read [domain rules](references/domain-rules.md) for the bounded method and schema,
[source map](references/source-map.md) for evidence requirements, and
[controls](references/controls.md) before preparing a result.

## Workflow

- Record authority type, lifecycle (`proposed`, `adopted`, `effective`, `stayed`, `withdrawn`, `superseded`, `unknown`), status-as-of and publication date. Keep commencement and compliance deadlines separate. Approved/adopted does not mean currently applicable.
- Entity, activity, product, threshold, exemption and cross-border nexus require an explicit supplied applicability assessment. Jurisdiction/business-line matching is only a screening hint. Missing review evidence remains `unknown`, including mismatching or absent scope facts.
- Review policy, control, system, data, training and owner mappings for applicable or unresolved obligations. A justified mapping exception is not silently treated as missing coverage.
- Only an active binding requirement, supplied applicable assessment, elapsed compliance deadline and sourced incomplete implementation produce an elapsed-deadline finding. Already effective is not synonymous with overdue; unknown implementation is unevaluable. Guidance and proposed/stayed changes do not generate legal-breach conclusions.
- Future deadlines produce readiness analysis. Declared authority conflicts are routed, not resolved or independently discovered by the calculator.

## Input, output and verification

`change_id`, `as_of`, `config_version`, `instrument`, extracted `obligations`, `firm_profile`, and optional `inventory.mappings`. Each non-unknown applicability assessment records status, rationale, source reference, reviewer and review date. Implementation assertions require a source reference.

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

`policy-procedure-gap-analyzer` owns deeper policy design comparisons; `contract-obligation-extractor` owns contractual requirements; `model-change-impact-analyzer` owns model changes; `enterprise-risk-assessment-builder` owns firm-wide risk. Privacy, reporting and exam packages consume scoped findings through their own validators.

No current regulatory corpus, horizon-monitoring scheduler, legal rule pack, operational integration or primary-text truth verification is bundled. All lifecycle and applicability evidence is supplied and subject to professional review.

Read [handoffs](references/handoffs.md) before transferring evidence. Apply source-specific
confidentiality, minimization and audience controls; SAR restrictions attach only when the
actual source/use warrants them, not to every generic compliance artifact.

Shared [evidence contract](references/evidence-contract.md) and [source governance](references/source-governance.md) define cross-workflow provenance and authority boundaries.
