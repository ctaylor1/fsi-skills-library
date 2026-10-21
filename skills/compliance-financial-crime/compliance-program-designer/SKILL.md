---
name: compliance-program-designer
description: >-
  Design a scoped compliance or financial-crime program from supplied mandates, exposures, control design, accountability and resource requirements. Use for a new program or material redesign; produces a reviewable design and unresolved dependency register.
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
  aws-fsi-owner: "Chief Compliance Officer / Financial Crime Program Owner"
  aws-fsi-primary-user: "Compliance professional / accountable institutional reviewer"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-10-03"
---

# Compliance Program Designer

Use when a new entity, activity or product needs a program design or the existing operating model needs material redesign. Produce a **Program design memorandum with mandate perimeter, risk-to-control coverage, accountability, resource gaps and a prioritized implementation backlog**. Interpret primary text and institution artifacts before constructing native input; the helper consumes reviewed extracted facts and supplies bounded checks. It does not independently perform professional review.

Read [domain rules and input schema](references/domain-rules.md), [source map](references/source-map.md) and [controls](references/controls.md). For another owner’s job, read [handoffs](references/handoffs.md).

## Professional workflow

- Establish the legal entities, activities, products, countries and governance perimeter from reviewed institution evidence. Obtain the actual mandate and sources of delegated responsibilities; a proposed organization chart does not prove authority.
- Enumerate material risk categories, exposure evidence and assessed applicability. Challenge absent sanctions, ML, TF, PF, bribery, conduct or other categories only against the supplied institution taxonomy; avoid imposing a universal taxonomy or statutory pillar list.
- Design preventive/detective controls with execution process, system/data dependencies, evidence produced, escalation and accountable roles. Separate design evidence from operating performance.
- Compare required resources with evidenced allocation in the same unit and scope. Document skill mix, capacity assumptions, training, access and technology needs; allocation arithmetic alone does not establish adequacy.
- Keep management operation, second-line monitoring, statutory independent testing and third-line audit mandates separately evidenced. Record reporting/escalation and reviewer independence dependencies.
- Produce the program design, open questions, sequencing and specialist handoffs. Human owners decide adequacy, budget, mandates and implementation acceptance.

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
