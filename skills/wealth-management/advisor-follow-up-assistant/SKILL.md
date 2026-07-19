---
name: advisor-follow-up-assistant
description: >-
  Draft a compliant post-meeting follow-up package for advisor approval: meeting notes/summary,
  action items with owners and due dates, a client communication (email/letter/portal message),
  required disclosures, proposed CRM field updates, and a next-meeting reminder — each material
  assertion mapped to a source and laid into the firm's approved template. Use when a financial
  advisor or client-service associate needs to turn a client review or meeting record into a
  review-ready follow-up, package the required disclosures for a recommendation discussed, or draft
  the client email and CRM update for sign-off. HARD BOUNDARY: draft-only. This skill NEVER sends
  or delivers the communication, writes the CRM or any system of record, schedules a meeting, places
  or stages a trade, makes a suitability/Reg BI determination, or guarantees performance. Every send,
  write, approval, and recommendation decision is left for a licensed human to adjudicate.
license: MIT
compatibility: Amazon Quick Desktop; requires CRM, portfolio-accounting/OMS, planning-engine, product-data, disclosures/restrictions, and approved-tax-assumptions MCP integrations (all read-only) plus the controlled follow-up template and disclosures library.
metadata:
  aws-fsi-category: "Wealth Management"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Draft & package"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Wealth Management advisory & compliance"
  aws-fsi-primary-user: "Financial advisor / client-service associate"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Advisor Follow-Up Assistant

## Purpose and outcome
Turn a documented client meeting into a complete, source-mapped **draft follow-up package** laid
into the firm's approved template: a meeting summary, action items (each with an owner and due
date), a client communication draft, the required disclosures for any recommendation discussed, a
**proposed** CRM update, and a next-meeting reminder. The outcome is a review-ready draft in which
every required section is present, every material assertion carries a citation, every discussed
recommendation is covered by its disclosure and routed for suitability review, and the advisor /
supervisory-principal approval block is recorded as **pending**. The send, the CRM write, the
suitability determination, the scheduling, and any trade all stay with licensed humans and
downstream skills.

## Use when
- "Draft the follow-up notes, action items, and a client email from today's review meeting."
- "Prepare a CRM update and a next-meeting reminder for the client I just met with, for my approval."
- "Package the meeting summary with the required disclosures for the recommendation we discussed."
- "Map each follow-up assertion to its source and flag anything unsupported before I sign off."

## Do not use
- **Sending the email or writing the CRM** → out-of-band human/operations steps after approval; this
  skill drafts and proposes only.
- **Suitability / Reg BI review** of a recommendation discussed → `suitability-reg-bi-reviewer`
  (this skill drafts and routes; it never approves suitability).
- **Building or refreshing the IPS** → `investment-policy-statement-builder`.
- **Preparing trades** to act on an action item → `portfolio-rebalancing-assistant` (R4, gated).
- **Comparing** competing proposals → `portfolio-proposal-comparator`.
- **Senior / diminished-capacity** concerns → `senior-investor-protection-screener`.
- Any request to **send, deliver, finalize, approve, schedule, or trade** → refuse; keep it a draft
  and route to the human approver.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This is the **drafting** step in a chain of
distinct control activities; it never performs the suitability review, sends the communication,
writes the CRM, or trades. It emits a durable `followup_id` + draft package for the advisor and
supervisory principal to adjudicate, and records routes to downstream skills where a recommendation
or a protection concern is involved.

## Inputs and prerequisites
- A documented meeting record and approved inputs: meeting date/attendees/channel, discussion
  points, any recommendations discussed (with `requires_disclosure` / `requires_suitability_review`
  flags), action items (owner, due date), the intended client communication (channel, subject, key
  points), the applicable disclosures, proposed CRM field changes, and the next-meeting target — a
  citation for each material item. Schema: [scripts/validate_input.py](scripts/validate_input.py).
- Read access to CRM/meeting record, planning engine, portfolio-accounting/OMS, product data, the
  disclosures/restrictions register, and the approved tax-assumptions set.
- The **versioned** approved follow-up template and disclosures library (versioned contracts).

## Source hierarchy
See [references/source-map.md](references/source-map.md). CRM/meeting record is the system of record
for the meeting and relationship; planning engine for objectives; portfolio-accounting/OMS for
holdings and drift; product data for instrument facts; the disclosures/restrictions register for
required disclosures. Cite every material assertion. Template and disclosures library are
**versioned contracts** recorded on the draft.

## Workflow
1. **Validate & normalize** — run `validate_input`; confirm required inputs, that each material item
   carries a source, and that each action item has an owner and due date. Flag anything missing as
   `needs-data`.
2. **Assemble the draft (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): lay inputs into the 7
   required template sections, build the section→citation source map, check **disclosure
   completeness** (every recommendation flagged `requires_disclosure` is covered) and record a route
   to `suitability-reg-bi-reviewer` for each recommendation flagged `requires_suitability_review`,
   route senior/vulnerable indicators to `senior-investor-protection-screener`, and score
   completeness. Anything unsupported or incomplete is surfaced, not smoothed over.
3. **Record approvals as pending** — write the Advisor and Supervisory Principal approval block with
   status `pending`; the draft is never self-approved.
4. **Set draft-only status** — `draft_status = draft`, `delivery_status = not-delivered`,
   `crm_write_status = not-written`.
5. **Validate the draft** — run [scripts/validate_output.py](scripts/validate_output.py); fix every
   finding or fail closed.
6. **Package, do not deliver** — emit the draft package keyed to
   [assets/output-template.md](assets/output-template.md) with the `followup_id`, source map, routes,
   gaps list, and standing note. Sending, CRM writes, scheduling, and any trade stay with humans.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py) after. The
output check enforces: all 7 required template sections present and titled; every material section
cited (no unsupported assertions); every recommendation flagged for disclosure is covered and every
one flagged for suitability review is routed; every action item has an owner, due date, and citation;
approvals recorded and still `pending`; `draft_status = draft`, `delivery_status = not-delivered`,
`crm_write_status = not-written`; no send / CRM-write / trade / suitability-approval / guarantee
language; and the standing note present. Fail closed on any miss.

## Human approval
`required`. This skill produces a **draft only**. The advisor owns the content and the
recommendation; a supervisory principal owns the communication and supervision sign-off (FINRA Rule
2210 principal approval of retail communications, Rule 3110 supervision). Nothing is sent, written to
the CRM, scheduled, finalized, or traded by this skill. Approvals are captured as a pending block for
humans to complete out-of-band.

## Failure handling
- **Missing / uncited input** → set `needs-data`, list exactly what is missing; never invent a
  discussion point, action item, disclosure, or citation to complete a section.
- **Action item without an owner or due date** → surface as `needs-data`; do not assign one by
  guessing.
- **Recommendation missing its required disclosure** → `needs-data`; the drafter never fabricates a
  disclosure or resolves suitability itself — it routes to `suitability-reg-bi-reviewer`.
- **Stale template / disclosures version** → stop and flag; both are versioned contracts.
- **Stale / conflicting sources** → cite both and flag; do not pick a winner.
- **Tool timeout** → return the partial draft with an explicit incomplete flag; assume no retry.

## Output contract
1. **Draft follow-up package** — the 7 required sections (see
   [references/domain-rules.md](references/domain-rules.md)) laid into the approved template, each
   with its citations.
2. **Action-items table** — id, owner, description, due date, citation.
3. **Disclosures** — each covering its recommendation by id; **routes** — suitability / protection
   handoffs recorded (not executed).
4. **Source map** — section → citations; **gaps list** — any `needs-data` items.
5. **Approval block** — Advisor / Supervisory Principal, each `pending`.
6. **Machine-readable** — the draft object keyed by `followup_id`, with `draft_status: draft`,
   `delivery_status: not-delivered`, `crm_write_status: not-written`.
7. **Standing note** — "Draft follow-up package for human review only; nothing has been sent to the
   client, no CRM or system of record has been updated, no trade has been placed, and no suitability
   determination has been made."
See [references/controls.md](references/controls.md).

## Privacy and records
**Highly Confidential — customer NPI/PII.** Mask client and account identifiers in output to what the
draft requires. Retain the draft, its source map, gaps, and the template/disclosures versions per
firm books-and-records (SEC/FINRA recordkeeping, including retention of communications with the
public). Log every read and each draft generation with the author identity. Do not place NPI in
identifiers or logs.

## Gotchas
- **Draft ≠ sent.** Producing a client email is not delivery; the advisor (and a principal where
  required) approves and sends it out-of-band. `delivery_status` stays `not-delivered`.
- **CRM updates are proposed, not written.** The package lists field changes for the advisor to
  apply; this skill never writes the system of record. `crm_write_status` stays `not-written`.
- **Every action item needs an owner and a due date.** An unowned or undated item is `needs-data` —
  the drafter never assigns one to "close it out."
- **A recommendation pulls in its disclosure and a review.** Discussing a recommendation requires the
  matching disclosure and a route to `suitability-reg-bi-reviewer`; the draft never calls it
  "suitable" or "approved."
- **No guarantees in client-facing text.** Guaranteed-return / no-downside / will-outperform language
  fails the output screen closed.
- **Versioned template & disclosures.** Record the template and disclosures versions on every draft so
  the artifact is reproducible and reviewable.
