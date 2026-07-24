---
name: client-rfq-preparation-brief
description: >-
  Assemble a preparation brief for a client RFQ — instrument summary, client context (tier,
  KYC/AML status, jurisdiction), surfaced suitability/eligibility flags, and prior-activity
  summary — and deterministically check it against the required-sections checklist, for a sales
  trader to review before responding. Use when a sales trader asks to "prep this RFQ", "build the
  client brief for this inquiry", "what should I know before I respond to this RFQ", or "flag any
  suitability issues on this client". HARD BOUNDARY: R3 draft/decision-support only — it NEVER
  quotes or sets a price, makes a firm bid/offer, commits or executes for the firm, or makes a
  suitability/eligibility determination; it surfaces flags and assembles context for a human.
  Routes pricing/hedging scenarios to pricing-hedging-scenario-calculator.
license: MIT
compatibility: Amazon Quick Desktop; requires CRM/client-context, instrument reference, and prior-activity MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Capital Markets"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Draft & package"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 5 - 2026 industry expansion"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Capital Markets operations & compliance"
  aws-fsi-primary-user: "Sales trader"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Client RFQ Preparation Brief

## Purpose and outcome
Given a client RFQ, deterministically assemble a preparation brief — instrument summary, client
context, surfaced suitability/eligibility flags, and prior-activity summary — and check it against
the required-sections checklist. A successful output is context a sales trader reviews before
responding; the price, any commitment, and every suitability determination remain the human's.

## Use when
- "Prep this RFQ", "build the client brief for this inquiry".
- "What should I know before I respond", "flag any suitability issues on this client".
- A trader needs a consistent, cited pre-response brief.

## Do not use
- The user wants a **price/quote or a firm bid/offer**, or to **commit/execute** → out of scope;
  the trader/desk acts.
- The user wants **pricing/hedging scenarios** → route to `pricing-hedging-scenario-calculator`.
- The user wants a **trade-idea evidence packet** → `trade-idea-evidence-packet`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Emits a brief with a durable `brief_id`; it
does not quote, commit, or decide suitability.

## Inputs and prerequisites
- The **rfq** (client_id, instrument), **client_context** (tier, kyc_status, jurisdiction,
  restricted_products), **prior_activity**, and a **checklist** (required_sections). Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Suitability policy is a versioned contract; this skill surfaces flags, it does not adjudicate.
  See [references/domain-rules.md](references/domain-rules.md).

## Source hierarchy
See [references/source-map.md](references/source-map.md). CRM is the client system of record;
instrument reference and prior-activity feeds provide context. Cite every flag and section to its
source.

## Workflow
1. **Validate input** — run `validate_input`; confirm the RFQ, client context, and checklist.
2. **Assemble (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): build the sections,
   surface suitability/eligibility flags (KYC status, restricted product, jurisdiction), summarize
   prior activity, and check required-section completeness.
3. **Assemble gaps/flags** — per gap/flag: section/reason, evidence, citation.
4. **Suggest disposition** — `ready-for-review` or `review-required` (a triage suggestion, not a
   suitability decision).
5. **Validate output** — run [scripts/validate_output.py](scripts/validate_output.py) for
   citation coverage, the no-pricing/no-commitment screen, and disclaimer.

## Validation loop
`validate_input` before, `validate_output` after. If a flag/gap lacks a citation, or the text
contains pricing/commitment language, **fix or fail closed**.

## Human approval
`required`: no price/quote, firm bid/offer, commitment, execution, or suitability determination
without the authorized human. The skill only prepares context and surfaces flags.

## Failure handling
- **Missing client context** → the suitability section is marked incomplete; never assume the
  client is eligible.
- **Restricted product / stale KYC** → surface as a flag with the rule, never resolve it.
- **Missing required section** → completeness gap; do not fabricate the content.
- **Stale/conflicting source** → cite both; escalate. **Tool timeout** → partial + incomplete flag.

## Output contract
1. **Summary** — RFQ id, client (masked), instrument summary, disposition.
2. **Sections** — instrument, client context, suitability review (flags), prior activity.
3. **Flags & completeness gaps** — each with reason + citation.
4. **Machine-readable** — sections + flags + gaps + `brief_id`.
5. **Standing disclaimer** — "Preparation brief only; not a quote, a price, a firm bid/offer, or a
   commitment of the firm, and not a suitability determination. Nothing has been priced or executed."
See [references/controls.md](references/controls.md).

## Privacy and records
Customer NPI/PII. Mask client identifiers (last 4). Retain brief + citations. Log read +
external-delivery approval. Never exfiltrate client data across the wall.

## Gotchas
- **A brief is not a quote.** Never state or imply a price, bid, or offer.
- **Surfacing a flag ≠ deciding suitability** — the trader/compliance decides; report the rule and
  the fact.
- **Prior activity is context, not a recommendation** to trade again.
- **Never commit the firm or imply execution.**
