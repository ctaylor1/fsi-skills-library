---
name: relationship-manager-client-briefer
description: >-
  Assemble a commercial relationship-manager (RM) client brief from approved sources: resolve
  the client entity and contacts, then draft a concise, fully source-cited brief covering
  credit exposures (with committed/outstanding tie-out), product holdings, profitability,
  covenant status, recent news and adverse-media flags, service issues, pipeline, cross-sell
  context, source dates, and open actions, from an approved template. Use when a commercial RM
  or portfolio manager needs a pre-meeting brief, a relationship one-pager, an account-review
  pack, or a consolidated client view across exposures, covenants, profitability, service
  issues, pipeline, and open actions. This skill NEVER sends, submits,
  distributes, or files the brief and never writes the CRM or any system of record; NEVER makes
  a credit, covenant, pricing, or risk-rating decision (breaches are surfaced, never waived);
  NEVER gives investment, legal, or tax advice; and states nothing a cited source does not
  support — it drafts a brief for human review.
license: MIT
compatibility: Amazon Quick Desktop; requires commercial-CRM, core-banking/loan-servicing, covenant-tracking, profitability, service/case-management, and news/media MCP integrations (all read-only; drafting only — no send, submit, file, or CRM write).
metadata:
  aws-fsi-category: "Banking"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Draft & package"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 2 - analytical production"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Banking product & credit operations"
  aws-fsi-primary-user: "Commercial relationship manager / portfolio manager"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Relationship-Manager Client Briefer

## Purpose and outcome
Turn a commercial client's approved relationship data into an audit-ready **RM client brief**:
resolve the client entity and contacts, then draft a concise, **fully source-cited** brief
covering exposures (with a committed/outstanding tie-out), product holdings, profitability,
covenant status, recent news and adverse-media flags, service issues, pipeline, cross-sell
context, source dates, and open actions — from an approved template. The outcome is a
review-ready pre-read (or a clear, itemized reason it cannot be assembled yet) that a human RM
reads, verifies, and — if they choose — uses or delivers. The skill never delivers or writes a
system of record, never decides or commits on credit/covenant/pricing/rating, and states
nothing a cited source does not support.

## Use when
- "Brief me on this client before the review / build me a relationship one-pager."
- "Pull together exposures, covenants, profitability, and open actions for this account."
- "Prepare an account-review pack: products, service issues, pipeline, and cross-sell context."
- "Give me a consolidated portfolio-client view with source dates and what's outstanding."

## Do not use
- **Drafting the credit / underwriting memo** for a new facility, renewal, or increase →
  `credit-memo-drafter`.
- **Testing covenants or working a breach/cure** beyond surfacing status →
  `covenant-compliance-monitor`.
- **Designing a treasury / cash-management proposal** → `commercial-cash-management-advisor`.
- **Onboarding** a new entity/product (document collection/checks) →
  `customer-onboarding-document-checker`.
- **Collections / delinquency** treatment → `collections-treatment-planner`; a **servicing
  exception** → `loan-servicing-exception-resolver`.
- **Adverse-media investigation** → `adverse-media-investigator`; **KYC/CDD refresh** →
  `kyc-customer-due-diligence-screener`; **risk-rating review** → `customer-risk-rating-reviewer`.
- Any request to **send/deliver, write the CRM, decide/approve credit, waive a covenant, price,
  re-rate, or advise** → refuse; draft only and route to a human or the skill above.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill is **prep-time drafting
only**. It consumes read-only context from the CRM, core banking/servicing, covenant tracking,
profitability, service, and news, and emits a `client_id`-keyed brief with
`reviewer_signoff_required` and a recorded `approvals` block. Credit memos, covenant work,
cash-management design, onboarding, collections, servicing, adverse-media/KYC/rating work,
delivery, and CRM writes belong to the routes above or to an authorized human.

## Inputs and prerequisites
- The client record: `client_id`, `legal_name`, `relationship_manager`, `entity_resolved`, and
  a per-client **source inventory**; plus the content lists — `exposures` (facility, committed,
  outstanding), `covenants` (name, status, test date), `profitability`, `products`,
  `service_cases`, `news` (adverse flag), `pipeline`, `contacts`, `cross_sell`, and
  `open_actions`. Every content item cites a `source_id` in the inventory. Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- An `as_of_date` (drives freshness and overdue-action calculations), a `freshness_days`
  threshold, and a tighter `critical_freshness_days` for exposures/covenants/profitability.
- Read access to CRM, core banking/servicing, covenant tracking, profitability, service, and
  news. No write, send, submit, or delivery capability is used.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The commercial CRM is the system of
record for client identity and contacts; core banking for exposures and products; covenant
tracking for covenant status; profitability for return metrics. **Cite every item** with
`{system}:{ref}@{date}`. Nothing enters the brief without a source; the approved brief template
is a **versioned contract**.

## Workflow
1. **Validate & normalize** — run `validate_input`; confirm each client is structurally
   complete and every content item cites a source in the inventory; flag gaps as warnings.
2. **Assemble deterministically** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): confirm required
   inputs, confirm the entity is resolved, check content-to-source integrity, screen source
   freshness (tighter for exposures/covenants/profitability), tie out committed/outstanding
   exposure, flag overdue actions, and surface covenant breaches and adverse news as **routing
   flags**. Rules: [references/domain-rules.md](references/domain-rules.md).
3. **Assign status** — `needs-data`, `unresolved-entity`, `unsupported-content`, or
   `stale-source` blocks assembly with an itemized reason; only a clean record becomes
   `draft-brief`.
4. **Draft the brief** — for a packageable client, assemble the brief from
   [assets/output-template.md](assets/output-template.md): identifiers, exposure summary,
   covenant status, profitability, products, service issues, news, pipeline, contacts,
   cross-sell context, open actions, routing, a citations index, and the recorded approvals +
   reviewer sign-off block. No statement without a cited source.
5. **Validate output** — run [scripts/validate_output.py](scripts/validate_output.py); fail
   closed on any miss (template fidelity, unsupported claims, exposure tie-out, recorded
   approvals, delivery/CRM-write, credit/covenant/pricing/rating decision, advice, standing
   note).
6. **Never deliver** — hand the reviewed draft to the human, who verifies and, if authorized,
   uses or delivers it and performs any CRM write or credit/covenant decision.

## Validation loop
Run `validate_input` before and `validate_output` after. The output screen enforces: template
fidelity (required sections, no unfilled placeholders); a packageable record is entity-resolved,
fully source-cited, and free of blocking stale critical sources; exposure totals tie out;
required approvals are recorded (`reviewer_signoff_required` + `approvals`); no delivery/
CRM-write, no credit/covenant/pricing/risk-rating decision, and no investment/legal/tax advice
language; standing note present. See [references/controls.md](references/controls.md). Correct
and re-run until it passes or the record is flagged not-packageable.

## Human approval
`external-delivery`. A human must review and authorize before the brief is delivered or any
system of record (CRM) is changed; where the brief informs a credit action, renewal, or
covenant matter, credit/risk review is required and recorded in the approvals block. This skill
proposes and drafts; it never delivers, writes, decides, approves, waives, prices, re-rates, or
advises. Internal drafting may be reviewer-sampled per [references/controls.md](references/controls.md).

## Failure handling
- **Missing required input** (no legal name, RM, or exposures) → `needs-data`; list exactly
  what is missing; do not invent a relationship or an exposure.
- **Unresolved entity** → `unresolved-entity`; a human confirms who the client is; never guess
  identity or a contact.
- **Content cites an unknown source** → `unsupported-content`; drop or substantiate the item;
  never fabricate an exposure, covenant status, figure, or news item to fill the brief.
- **Stale source** (older than its freshness threshold, unacknowledged) → `stale-source`;
  refresh or acknowledge it; never present stale exposure/covenant/profitability as current.
- **Tool timeout / partial context** → return partial output with an explicit incomplete flag
  and the sources used; no retry assumption.

## Output contract
1. **Client queue** — per client: `client_id`, legal name, status, `packageable`, and a
   one-line reason.
2. **Client brief** (per packageable client) — identifiers, exposure summary (tie-out),
   covenants, profitability, products, service issues, news, pipeline, contacts, cross-sell
   context, open actions, routing flags, a citations list, `reviewer_signoff_required: true`,
   and a recorded `approvals` block, following [assets/output-template.md](assets/output-template.md).
3. **Blocked list** — each non-packageable client with its itemized reason(s).
4. **Machine-readable** — the brief records keyed by `client_id` with `as_of_date`.
5. **Standing note** — "Relationship-manager client brief for internal preparation only; this
   skill does not send, submit, distribute, or file the brief and does not write any CRM or
   system of record, does not make or communicate any credit, covenant, pricing, or risk-rating
   decision, gives no investment, legal, or tax advice, and every item must be verified against
   its cited source before use."

## Privacy and records
**Highly Confidential (customer NPI/PII).** Include only the relationship context the brief
needs (data minimization); do not pull unrelated customer data into a brief. Respect the
classification of each source and do not elevate restricted content into a wider-distribution
pack. Retain the draft brief, the `as_of_date`, template version, and source citations with the
client record; log every read and every brief produced with the preparer identity. Delivery and
any CRM write are human actions outside this skill.

## Gotchas
- **Drafting ≠ delivering.** The brief is a pre-read draft; a human uses or delivers it. Never
  emit "brief sent / CRM updated / logged the call" language or imply anything was delivered.
- **Surface, never decide.** The brief may restate a *sourced* covenant status ("fixed-charge
  coverage breached at 2026-06-30 [cite]"); it must never waive, cure, approve, decline, renew,
  price, or re-rate. Breaches and at-risk covenants are routed for credit/risk review.
- **Every line needs a source.** A confident figure with no citation is an unsupported claim
  and is stripped by the output screen — no exposure, covenant, metric, news item, or action
  without a `source_id`.
- **Exposures tie out.** Committed/outstanding totals must equal the sum of the facility lines;
  a mismatch fails closed. Exposures are reported, not projected.
- **Critical freshness is tighter.** Exposure/covenant/profitability sources go stale in
  `critical_freshness_days` (default 10); a stale critical source blocks unless acknowledged.
- **Cross-sell is context, not advice.** Surfacing a sourced product-gap option is fine;
  telling the client what to buy, sell, refinance, or hedge is advice and is prohibited.
- **Adverse news is a flag, not a verdict.** Surface and route adverse media; never conclude a
  financial-crime or reputational finding here.
