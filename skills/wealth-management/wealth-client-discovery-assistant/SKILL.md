---
name: wealth-client-discovery-assistant
description: >-
  Build a source-linked household fact-find from documented client interviews and records:
  household members, financial and personal context, goals, engagement scope, and explicit
  information gaps. Use when a wealth advisor or client-service associate conducts discovery,
  refreshes client facts, or prepares an intake handoff. Preserves reported facts without
  verifying identity, deciding KYC, assessing investment suitability, recommending, or writing systems.
license: MIT
compatibility: Amazon Quick Desktop; requires approved read-only CRM/interview, client-document, and engagement-record integrations. Bundled Python uses supplied JSON only; no live integrations or network access.
metadata:
  aws-fsi-category: "Wealth Management"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Draft & package"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 6 - wealth management P0"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); approved additional jurisdiction packs required before use"
  aws-fsi-owner: "Wealth Management advisory & client operations"
  aws-fsi-primary-user: "Wealth advisor / client-service associate / financial planner"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-09-16"
---

# Wealth Client Discovery Assistant

## Purpose and outcome
Produce a household fact-find that preserves what the client reported, what documents support,
and what remains unknown. The output is an intake artifact for human review, not a verified
client profile or permission to advise or open an account.

## Use when
- Prepare a fact-find from a client discovery interview and approved records.
- Refresh household facts after a life event without inferring missing information.
- Show which household planning areas were collected, reported absent, or not collected.

## Do not use
- Identity verification, KYC/CDD, onboarding approval, or account opening.
- Household balance reconciliation, investment-risk profiling, or investment recommendations.
- Drafting legal/tax conclusions or supplying missing amounts, dates, priorities, or authority.
Route these jobs using [references/handoffs.md](references/handoffs.md).

## Adjacent-skill handoffs
Pass the household ID, artifact ID, source registry, and unresolved findings. Discovery records
client assertions; downstream onboarding, reconciliation and risk profiling independently check
what their decisions require. A cited statement of authority is not an authorization token.

## Inputs and prerequisites
Use the `wealth-p0-v1` envelope and domain schema in
[references/domain-rules.md](references/domain-rules.md). The supplied registry must include
source owners, observation dates, and validity dates. Each member, fact, goal, coverage row,
household record, and engagement context has its own `source_ids`. Minimize identifiers before intake.

## Source hierarchy
The firm's engagement record supplies engagement scope/capacity; dated approved records supply
documented facts; the client interview supplies client-reported context. Do not promote a client
assertion to verified fact. See [references/source-map.md](references/source-map.md).

## Workflow
1. Extract only supported facts into the structured intake; retain source locators and the
   distinction between `client-reported` and `documented`.
2. Run [scripts/validate_input.py](scripts/validate_input.py). Stop on malformed or invalid
   envelope/registry data; obtain current evidence rather than overriding the source dates.
3. Run [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py). It preserves
   substantive records, identifies missing facts and conflicting coverage, and binds the output
   to the complete input snapshot. It does not infer a fact or calculate a financial plan.
4. Run [scripts/validate_output.py](scripts/validate_output.py). Produce the fact-find following
   [assets/output-template.md](assets/output-template.md), including every unresolved finding.
5. An advisor verifies source support and corrections before the artifact is consumed elsewhere.

## Validation loop
The output checker validates the common envelope and independently rebuilds the fact-find from
its retained source snapshot, checking substantive values, identities, numeric fields, counts,
and missingness. A valid `needs-data` artifact is a correct gap report, not a complete fact-find.
The checks validate supplied metadata and reproducibility; they do not prove source truth,
professional approval, semantic extraction accuracy, or regulatory compliance.

## Human approval
Human review is required. No KYC conclusion, recommendation, approval, external delivery,
CRM update, or account action occurs. See [references/controls.md](references/controls.md).

## Failure handling
- Missing/unknown item sources, unknown member links, duplicate IDs, or uncollected areas:
  preserve the supplied records and emit findings with `status: needs-data`.
- Missing, stale, or future-dated registry evidence; unsupported jurisdiction; malformed input:
  stop with input errors. Do not output a review-ready envelope.
- An absent amount is unknown, never zero. An absent topic is uncollected, never “none.”
- Source conflicts remain unresolved questions for the advisor; never choose silently.

## Output contract
Common envelope: `request_id`, `household_id`, `as_of`, engagement, source registry, input hash,
artifact ID, status, findings, and fixed draft/no-action flags. `result` preserves household,
members, facts, goals, engagement details, coverage, counts, input snapshot, and handoff context.
The hash binds this derivative artifact to its supplied inputs; it grants no authority.

## Privacy and records
Use masked names and opaque household/member IDs. Retain the minimum necessary input snapshot,
source locators, output and corrections in approved storage under firm policy. No live storage
integration exists here; the scripts read JSON and write results only to standard output.

## Gotchas
- Being a spouse, trustee, or entity representative does not itself establish decision authority.
- A client reporting no debt is different from a blank debt section.
- Goal dates and priorities can remain unspecified; do not invent precision.
- Discovery evidence can be sufficient to record an assertion and insufficient to open an account.
