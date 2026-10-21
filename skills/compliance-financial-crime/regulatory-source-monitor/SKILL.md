---
name: regulatory-source-monitor
description: >-
  Compare supplied dated baseline/current regulatory-source snapshots and build a change docket with missed-source coverage, legal lifecycle and supersession chronology. Use for horizon scanning evidence; no live feed, scheduler, legal interpretation or alert dispatch is bundled.
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
  aws-fsi-owner: "Regulatory Intelligence / Regulatory Change Management"
  aws-fsi-primary-user: "Compliance professional / accountable institutional reviewer"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-10-03"
---

# Regulatory Source Monitor

Use when dated regulatory snapshots need comparison or a horizon-scanning coverage docket is required. Produce a **Source coverage register and event docket with additions, revisions, withdrawals, supersession links, date distinctions and missed-source questions**. Interpret primary text and institution artifacts before constructing native input; the helper consumes reviewed extracted facts and supplies bounded checks. It does not independently perform professional review.

Read [domain rules and input schema](references/domain-rules.md), [source map](references/source-map.md) and [controls](references/controls.md). For another owner’s job, read [handoffs](references/handoffs.md).

## Professional workflow

- Define the expected source universe, as-of, collection window and evidence retrieval outcome for each source. An inaccessible feed is uncovered; zero extracted events from a covered source is a supplied collection result, not proof of no legal developments.
- Retain separate baseline and current snapshots with source IDs, versions, instrument IDs, text/content hashes, observation times and actual publication/effective/compliance dates. Verify instrument identity before matching versions.
- Compare by source and instrument ID; report new, revised and missing-current observations. A disappeared item is not legally withdrawn without an explicit source-backed lifecycle event.
- Preserve proposals, adoptions, effectiveness, stays, withdrawals and supersession as supplied legal states. Record replacement IDs and missing predecessor/current links; publication and effective date are not interchangeable.
- Identify missed source collections, truncated/partial retrieval, late observations and chronology conflicts before declaring coverage. No currently maintained legal corpus or complete-source guarantee is included.
- Package the dated docket for regulatory change impact review. Scheduling, network acquisition and external notifications need separately authorized adapters.

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
