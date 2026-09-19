---
name: client-review-preparer
description: >-
  Assemble a source-linked pre-meeting wealth client-review pack: household accounts, holdings and value tie-outs, reported performance, goals, planning context, open actions, an agenda, a brief and a deck outline. Use for annual, semiannual or ad-hoc advisor reviews. Requires explicit engagement, current source evidence and approved disclosure policy. Drafts only; never recommends, decides suitability, trades, delivers or writes a system of record.
license: MIT
compatibility: Amazon Quick Desktop; requires wealth-CRM, portfolio-accounting/custody, performance, planning-engine, and product/disclosure MCP integrations (all read-only; drafting only — no recommendation, trade, delivery, or system-of-record write).
metadata:
  aws-fsi-category: "Wealth Management"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Draft & package"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 6 - wealth management P0"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "existing-updated"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Wealth Management advisory & compliance"
  aws-fsi-primary-user: "Wealth advisor / client-service associate / financial planner"
  aws-fsi-version: "0.2.0"
  aws-fsi-recertification-date: "2027-09-16"
---

# Client Review Preparer

## Purpose and outcome
Assemble a pre-meeting household review pack from supported records: a brief, agenda and deck
outline with account/household value tie-outs, reported performance, goals, planning items,
meeting/service history, life events, open actions and applicable disclosures. This skill packages
existing evidence; it does not calculate goal progress or recommend investments.

## Use when
Prepare an annual, semiannual or ad-hoc client review, a sourced meeting brief/agenda, or a household
review deck outline for an advisor, client-service associate or financial planner.

## Do not use
Recommendation review, goal/retirement modeling, IPS drafting, proposal comparison, trading, client
protection investigations, post-meeting follow-up, delivery or CRM writes. Route those jobs using
[references/handoffs.md](references/handoffs.md).

## Adjacent-skill handoffs
The pack is keyed by durable request, review-occurrence and household IDs. Preserve its evidence
snapshot and unresolved statuses. Surface handoffs; no downstream action or authorization occurs.

## Inputs and prerequisites
Use the v0.2 request contract in [references/domain-rules.md](references/domain-rules.md): explicit
versions, engagement capacity, approved disclosure/review-role policy, source owners/validity,
account identity and amounts, review IDs, and item-level source references. The approved policy
selects requirements for the engagement and review type; there is no universal disclosure default.

## Source hierarchy
CRM supplies relationship context; custody/accounting supplies accounts/values/holdings;
performance supplies reported returns; planning supplies goals; controlled libraries supply
current disclosures/templates. See [references/source-map.md](references/source-map.md).

## Workflow
1. Run [scripts/validate_input.py](scripts/validate_input.py). Resolve structural, identity,
   date, version and applicability errors; never invent values to pass.
2. Run [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py). Missing business
   information, unresolved identities, unsupported items, stale observations, value breaks and
   missing disclosures produce explicit blocked records; only complete records are packaged.
3. Run [scripts/validate_output.py](scripts/validate_output.py). It rebuilds from the retained
   input snapshot and compares actual content, identity, values, coverage and artifact lineage.
4. Present the brief/agenda/deck outline using [assets/output-template.md](assets/output-template.md).
   A human checks each material assertion against the underlying source and applicable firm policy.

## Validation loop
Correct source records or preserve the blocking status; do not edit calculated output to make it
pass. Deterministic checks establish consistency with supplied records, not source truth, semantic
support, legal applicability or professional approval. The human review remains a production gate.

## Human approval
R3, required review. Configured human roles must adjudicate before use or external delivery.
This package never grants approval, recommends, trades, sends, files, closes or writes a system.
See [references/controls.md](references/controls.md).

## Failure handling
Malformed input, missing/future/expired source dates, unsupported review type, missing policy or
versions stop assembly with needs-data errors. Business gaps remain individual blocked records.
Source-age exceptions require a named reviewer and reason and cannot extend expired validity.
On integration timeout, preserve partial evidence and report incomplete context; no silent retries.

## Output contract
Source snapshot, input hash, stable artifact ID, request/prior-artifact lineage, versioned context,
review queue, blocked reasons and full per-review pack. Each packageable pack includes substantive
brief and deck-outline content, supplied discussion questions, source citations, tie-outs and
pending configured review requirements. Hashes are evidence identifiers, not authorization tokens.

## Privacy and records
Use masked household/account references and minimum necessary context. The input snapshot is
sensitive evidence: keep it within approved storage and recipients under firm retention policy.
No external records are written by the bundled scripts.

## Gotchas
- An unknown review type must not select an empty disclosure policy.
- An absent amount is not zero; an absent source date is not fresh.
- Account values and holdings must use the same approved valuation/currency convention; this
  package does not reconcile FX, private-asset valuation dates or held-away coverage.
- Preparing the pack is distinct from recommendation review and actual meeting outcomes.
