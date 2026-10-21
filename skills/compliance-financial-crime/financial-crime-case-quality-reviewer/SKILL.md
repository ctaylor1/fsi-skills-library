---
name: financial-crime-case-quality-reviewer
description: >-
  Review supplied financial-crime case workpapers or case batches against explicit QA criteria for exhibits, chronology, reasoning, counterevidence, disposition traceability and versioned tool-output source faithfulness. Preserve untested cases and source gaps; prepare human-owned operational QA or second-line monitoring drafts without assurance opinions, case closure or reporting decisions.
license: MIT
metadata:
  aws-fsi-runtime: "Offline Python 3.10+ standard library and supplied JSON; no bundled connector or live action"
  aws-fsi-category: "Compliance & Financial Crime"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Restricted; source-specific confidentiality and audience limits"
  aws-fsi-jurisdictions: "Supplied reviewed jurisdiction and institutional legal profile; no default applicability"
  aws-fsi-owner: "Financial Crime Case Quality Lead / Mandated Oversight Owner"
  aws-fsi-primary-user: "Mandated case-quality reviewer and accountable professional owner"
  aws-fsi-version: "0.1.0"
  aws-fsi-release-date: "2026-10-04"
  aws-fsi-recertification-date: "2027-10-04"
---

# Financial Crime Case Quality Reviewer

Prepare a source-bound case-quality draft for a specific supplied mandate and period.
Read [domain rules](references/domain-rules.md) and [input contract](references/input-schema.md)
for case-native identities, criteria and evidence fields. Read [controls](references/controls.md),
[source map](references/source-map.md) and [handoffs](references/handoffs.md) before using or transferring evidence.

## Review method

Bind the exact institution, legal entity, jurisdiction, case-native IDs, upstream artifact
versions, review period, selected sample and population. Require the supplied mandate owner,
reviewer, legal profile and authority evidence. A role label proves neither identity nor independence.
Operational QA, second-line monitoring, statutory independent testing, audit and model validation
are different mandates. This method supports the first two; refer the others to their named owners.

Apply the supplied versioned criterion to each applicable case. Reconcile required exhibits and
exact source-fact locators; check event dates and predecessor chronology; retain material concerns,
contradictions and counterevidence; link the proposed disposition to the exact reviewed reasoning.
The method verifies explicit linkage and source consistency. A qualified human evaluates the
substantive reasoning and states a case-specific rationale; the script does not score keywords or
infer narrative adequacy. Supplied human judgment remains unverified.

Versioned external tool, model or copilot outputs may be checked under an explicitly selected
source-faithfulness criterion. Require output/model/prompt versions, proposed-fact locators and
human review. Compare proposed factual values with the exact supplied facts. This is case QA,
with no model validation, automated decision, legal-privilege or reputation determination.

## Draft and validation

Report observed criterion pass/fail/unknown counts and every case's coverage. Unknown or untested
is never pass. A partial case retains known exceptions and remains outside the complete-case
proportion denominator. Publish an exact numerator/denominator and decimal display only when
sample scope, sampling rationale and evidence are consistent. A convenience or risk sample does
not establish population prevalence. Thresholds require source-bound exact decimal strings;
comparisons use the exact ratio. Failures remain visible even within the supplied tolerance.

Use [output contract](references/output-schema.md) and the [human narrative template](assets/output-template.md).
Retain the detached original input and validate the native result before attaching narrative.
Native outputs carry draft/human-review/action-false controls; additional native narrative or
edited fields fail exact reconstruction. Source facts and proposed narratives remain unverified.

```sh
python3 -B scripts/validate_input.py INPUT.json
python3 -B scripts/calculate_or_transform.py INPUT.json > OUTPUT.json
python3 -B scripts/validate_output.py OUTPUT.json --input INPUT.json
python3 -B scripts/test_phase3.py
python3 -B scripts/run_evals.py
```

## Owner boundary

The Financial Crime Case Quality Lead / Mandated Oversight Owner accepts the mandate, sample,
criteria and findings. Authorized investigation/reporting owners decide escalation, closure,
reportability and filing. This package issues no assurance opinion, guilt conclusion, SAR decision
or filing, case closure, privilege determination, access grant or external disclosure. No claimed
user approval enables live action. SAR-restricted native evidence requires the authorized_fiu
recipient and compatible source permissions; do not produce an external projection. Mixed
restricted sources require a separately reviewed adapter.

The pinned [foundation contract](references/foundation-contract.md), [evidence contract](references/evidence-contract.md)
and [source governance](references/source-governance.md) govern portability, source limits and handoffs.
Bounded synthetic checks do not prove source authentication, professional acceptance or production readiness.
