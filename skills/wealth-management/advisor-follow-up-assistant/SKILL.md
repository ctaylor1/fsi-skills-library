---
name: advisor-follow-up-assistant
description: >-
  Prepare a source-linked post-meeting follow-up package for a wealth advisor: documented outcomes, owned and dated actions, client communication, disclosures, proposed CRM fields and a next-meeting reminder. Use after a documented client meeting. Requires item-level citations and current engagement/communications policy. Drafts only; never sends, writes CRM, schedules, trades or grants professional approval.
license: MIT
compatibility: Amazon Quick Desktop; requires CRM, portfolio-accounting/OMS, planning-engine, product-data, disclosures/restrictions, and approved-tax-assumptions MCP integrations (all read-only) plus the controlled follow-up template and disclosures library.
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
  aws-fsi-primary-user: "Financial advisor / client-service associate"
  aws-fsi-version: "0.3.0"
  aws-fsi-recertification-date: "2027-09-16"
---

# Advisor Follow-Up Assistant

## Purpose and outcome
Turn documented meeting outcomes into a source-linked draft: meeting summary, owned/dated action
items, an actual client-communication body, applicable disclosures, proposed CRM changes and a
next-meeting reminder. Retain the household and attendee context. No action is executed.

## Use when
An advisor or client-service associate needs a follow-up package, client email/letter/portal draft,
proposed CRM fields or documented next steps after an actual meeting.

## Do not use
Pre-meeting review preparation, investment recommendations, recommendation approval, IPS drafting,
trading, delivery, scheduling or CRM writes. See [references/handoffs.md](references/handoffs.md).

## Adjacent-skill handoffs
Keep the follow-up/meeting/household and artifact IDs. Route recommendation evidence to
`investment-recommendation-evidence-reviewer` and client communication to
`communications-compliance-reviewer`. Post-meeting outcomes, not the pre-read, govern this artifact.

## Inputs and prerequisites
Use [references/domain-rules.md](references/domain-rules.md). The v0.2 request requires household,
meeting ID/date/attendees, engagement capacity, dated owned source registry, versioned template and
disclosure references, and the approved communication policy with required review roles.
Every material discussion, recommendation, action, communication key point and CRM field has its
own resolvable citation. Empty operational sections require a cited not-applicable reason.

## Source hierarchy
The documented meeting governs what was discussed or agreed. Planning/portfolio/product sources
supply their own referenced facts. Firm-controlled template, disclosure and communication policy
sources govern presentation and review requirements. See [references/source-map.md](references/source-map.md).

## P5 source and recipient quality gate
Before treating model-created structured input or a recipient draft as reviewed,
follow [references/quality-gate.md](references/quality-gate.md). Inventory every
input field against detached source evidence and obtain a separate reviewer’s
field decisions. Preserve unknowns as null; a missing review stays pending.
Never create your own independent reviewer identity or approval to pass a gate.
Create one draft per exact recipient set, including internal colleagues, from the
supplied access registry. Keep the full input, review receipt and withheld details
in a separate restricted work area. Run the combined gate and verify the actual
final bytes before handoff; native calculator validation alone is insufficient.
If no independent reviewer or permission registry is available, deliver a clearly
pending internal working draft and the missing-evidence list to the authorized
reviewer. Do not describe it as cleared for any wider audience.

## Workflow
1. Run [scripts/validate_input.py](scripts/validate_input.py); stop on structural or invalid
   registry/version/applicability data. Preserve material gaps rather than guessing.
2. Run [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py). Each material gap
   becomes needs-data. It preserves actual content, constructs the communication body only from
   cited supplied key points, records evidence routes, and assigns configured approvals as pending.
3. Run [scripts/validate_output.py](scripts/validate_output.py). It independently rebuilds the
   artifact from its snapshot, verifies substantive content and item-level evidence, and rejects
   incomplete drafts at the ready-for-review gate.
4. Present the package using [assets/output-template.md](assets/output-template.md). A human
   verifies source support and approves any subsequent delivery/system activity separately.

## Validation loop
Fix the source request and regenerate, or present an explicitly incomplete gap report. Supplied
citation metadata and reproducibility do not establish semantic source support or compliance.
Human/adversarial real-model review remains required beyond the deterministic fixtures.

## Human approval
R3 draft-only. The approved engagement/communication policy identifies required human roles;
each remains pending. Do not assume every correspondence requires the same principal workflow.
See [references/controls.md](references/controls.md).

## Failure handling
Missing item citations, owners, dates, substantive content, or reviewed recommendation flags
produce needs-data. Missing versions, stale/future source dates, unsupported jurisdiction/capacity
or malformed structure stop assembly. Uncollected information is never supplied by inference.
Timeout/partial meeting records remain incomplete; do not silently retry or claim delivery.

## Output contract
Seven sections with substantive content, household/meeting identity and attendees, a communication
body, actions, disclosures, proposed CRM values, reminder, handoffs, configured pending approvals,
findings and source map. The artifact retains its input snapshot, hash, request/prior-artifact
lineage, versioned context and fixed no-action/no-delivery/no-CRM-write flags.

## Privacy and records
Minimize and mask client/account identifiers. Keep the sensitive source snapshot and derived
communication within approved retention/access boundaries. The scripts use local JSON and stdout;
no live CRM, communication, recordkeeping or calendar integrations are shipped here.

## Gotchas
- Another citation in the same section does not support an uncited assertion.
- A recommendation's disclosure/review flags must be explicitly supplied; missing is not false.
- A draft communication is not evidence that the client accepted it or received a disclosure.
- A cited no-action outcome is valid; do not invent a task to fill the template.
