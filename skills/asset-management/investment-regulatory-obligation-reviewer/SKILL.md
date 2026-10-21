---
name: investment-regulatory-obligation-reviewer
description: "Legacy supplied obligation mapping; explicit entity/activity/product/investor/territory jurisdiction profiles and primary-source bindings; no legal applicability determination. Draft-only; use explicit extension and detached source validation."
license: MIT
compatibility: Python 3.10+ offline supplied JSON. Engines, data rights and professional acceptance are deployment dependencies.
metadata:
  aws-fsi-category: "Asset Management"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 7 - asset management foundations"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "existing-updated"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (MNPI / client-confidential)"
  aws-fsi-jurisdictions: "Explicit supplied scope; no universal jurisdiction pack"
  aws-fsi-owner: "Asset Management investment & product"
  aws-fsi-primary-user: "Institutional investment professional / control reviewer"
  aws-fsi-version: "0.2.0"
  aws-fsi-recertification-date: "2027-10-04"
---

# Investment obligation applicability

## Select the supplied contract

The original request without an `extension` key preserves the original rule-pack method below.
For a cross-border or multi-profile comparison, set `extension: jurisdiction-profile-comparison`
on the foundation request and read [jurisdiction profile schema](references/jurisdiction-schema.md)
and [jurisdiction workflow](references/jurisdiction-workflow.md). The extension has a distinct
native schema; it does not convert an old rules request automatically. Unknown extensions fail.

Use the [jurisdiction source guide](references/jurisdiction-sources.md) to obtain the actual
versioned primary text and reviewed entity/activity/product/investor conditions. Geography
alone does not establish applicability, permission to market, or an exemption. Preserve
different deadlines and overlapping versions for the legal owner; never select a presumed
stricter rule automatically. Native outputs are internal drafts with detached original-input
validation. No profile outcome is a legal conclusion, discharge confirmation or market-access approval.

## Original supplied-rule review

Use this package when the requested job is to evaluate a supplied reviewed investment rule pack against explicit entity facts, jurisdiction, activities and effective dates. Separate applicable, inapplicable, proposed and unresolved obligations; never infer a legal conclusion or certify compliance.

Read [input and method rules](references/domain-rules.md) before constructing the native request;
[the source map](references/source-map.md) distinguishes supplied assertions from authoritative evidence.
Use [handoffs](references/handoffs.md) for adjacent jobs and [controls](references/controls.md) for review limits.

1. Establish the institution/portfolio identity, currency, economic date, knowledge cutoff and professional role.
2. Obtain the supplied policy/model/holdings inputs listed in the schema. Missing facts remain unknown; never invent a rate, exposure, legal classification or approval to complete a request.
3. Run `python scripts/validate_input.py INPUT.json`, then `python scripts/calculate_or_transform.py INPUT.json`. Rejected sources require corrected evidence. Review gaps remain visible in the draft.
4. Reconcile the results to independently sourced benchmarks or manual calculations using the documented method. An unavailable engine is an explicit gap; do not replace it with a simplified undisclosed model.
5. Run `python scripts/validate_output.py OUTPUT.json --input INPUT.json` against the separately retained original. This binds supplied inputs and outputs without authenticating their truth.
6. Prepare the [review packet](assets/output-template.md), retain unresolved issues and obtain the named professional review. The native result is immutable; any narrative or publication projection needs separate evidence review.

Do not use this package to perform trades, approve a policy, determine personal tax advice,
certify compliance, publish claims or write a system of record. It creates an internal draft.
Its concrete method is `supplied-rule-applicability`. Limitations: Synthetic eval thresholds are not law; deploy only reviewed current primary rule packs. No universal legal interpretation, regulatory filing or compliance certification.

Run `python scripts/selftest.py` for independently expected arithmetic and boundary cases.
Generated helpers are pinned by the repository's shared-resource lock; do not edit bundled copies.
