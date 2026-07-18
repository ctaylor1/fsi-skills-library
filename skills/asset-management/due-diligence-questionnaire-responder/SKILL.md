---
name: due-diligence-questionnaire-responder
description: >-
  Draft responses to due-diligence questionnaires (DDQs) and RFPs from an approved content
  library, firm policies, reconciled performance/risk data, and prior answers — attaching a
  citation, content owner, and effective date to every answer, flagging stale content, and
  routing unsupported questions to their owners. Use when an investor-relations, RFP,
  client-service, or compliance user needs to fill a DDQ/RFP, reuse approved answers, map
  questions to library content, flag stale or unsupported items, or produce a source-linked
  draft response with an open-items list. HARD BOUNDARY: draft-only — this skill never
  fabricates an answer for a question with no approved, in-date source; never drafts from
  unapproved (draft/in-review/expired) content; never adds a performance or return guarantee
  or any claim absent from the approved source; never certifies the response complete or
  final; and never sends, submits, or delivers it to a client, investor, or consultant.
  Content owners and compliance approve; a human delivers.
license: MIT
compatibility: Amazon Quick Desktop; requires controlled-content-library, approved-source (policy) retrieval, performance/risk-data, document-generation, and permission/approval-broker MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Asset Management"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Draft & package"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 2 - analytical production"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (MNPI / client-confidential)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Asset Management investment & product"
  aws-fsi-primary-user: "Investor relations / RFP team / client service / compliance"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Due Diligence Questionnaire Responder

## Purpose and outcome
Turn a DDQ or RFP — a list of questions from a client, investor, or consultant — into ONE
**source-linked draft response** assembled only from **approved** content. For each question
the skill matches an approved content-library or prior answer, sets a response status
(`drafted`, `stale`, `unapproved-source`, `data-gap`, or `unsupported`), attaches the content
owner, effective date, and citation (plus any performance/data-point citation), injects the
required disclosures, captures recorded approvals and outstanding required approvals, and
compiles an explicit open-items list routing every unsupported/stale/data-gap/unapproved
question to its owner. The outcome is a response a human can review and route: a rendered
response from [assets/output-template.md](assets/output-template.md) plus a machine-readable
manifest. The skill **drafts from approved content**; it does not author new content, clear
disclosures, or deliver anything.

## Use when
- "Draft responses to this DDQ / fill this RFP from our approved answer library and prior answers."
- "Map these questionnaire questions to approved content and cite each answer."
- "Flag any answers that are stale or that we don't have approved content for."
- "Reuse last quarter's approved answers where they still apply, with owners and dates."
- "Produce a source-linked DDQ draft with an open-items list for the content owners."

## Do not use
- **Fund/strategy commentary** narrative → `fund-commentary-drafter`.
- **Fund fact sheet** production → `fund-fact-sheet-builder`.
- **Performance / attribution** computation (source figures, not drafting) → `performance-attribution-builder`.
- **Portfolio exposure** analysis → `portfolio-exposure-analyzer`.
- **Mandate / guideline** testing of portfolios or trades → `mandate-compliance-monitor`.
- **Data-room diligence pack** assembly (buy-/sell-side) → `due-diligence-packager`.
- **Client-review brief / deck** → `client-review-preparer`.
- **Conflicts-of-interest** determination → `conflicts-of-interest-reviewer`.
- Any request to **fabricate an answer, use unapproved content, guarantee performance,
  certify the response complete, or send/submit it** → refuse; route to owners and a human.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Drafting is deliberately separated from
content ownership, compliance review, and external delivery (distinct controls, entitlements,
and accountability). This skill emits a durable `questionnaire_id` + drafted manifest and
hands off to `communications-compliance-reviewer` for the required-disclosure /
prohibited-claim review; unsupported questions route to their human content owners. It must
not perform the reviewer's or the owner's work.

## Inputs and prerequisites
- The intake bundle: `questionnaire_id`, product/strategy, jurisdiction, `as_of_date`, the
  masked client, the `content_library` (each answer with topic, owner, effective/expiry dates,
  `approval_status`, `source_ref`, optional `data_refs`), `prior_answers`, `data_points` (with
  `as_of`/`expires`/owner), `required_disclosures`, `required_approvals`, recorded `approvals`,
  and the `questions` (each with section, text, topic, optional `matched_answer_id` and
  `data_request`). Schema and required fields: [scripts/validate_input.py](scripts/validate_input.py).
- Read access to the controlled content library, policy retrieval, performance/risk data, and
  the approval broker (all read-only). No answer is fabricated: what has no approved, in-date
  source becomes an open item routed to an owner.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The controlled content library is the
system of record for what an approved answer is; policies and performance/risk data are the
sources a library answer cites; prior answers are used only when no library entry supplies the
topic. Cite every drafted item as `{system}:{ref}@{date/version}`. The content library, the
required-disclosure register, and the response template are **versioned contracts**.

## Workflow
1. **Validate & normalize** — run `validate_input`; confirm the intake structure and surface
   data gaps (questions with no approved answer, expired content, missing data points,
   unrecorded required approvals) as warnings.
2. **Draft the response (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): match each question
   to a single approved answer, set its status, attach owner + effective date + citations,
   inject required disclosures, capture recorded approvals + outstanding required approvals, and
   build the citation source index. Rules: [references/domain-rules.md](references/domain-rules.md).
3. **Render the response** — populate [assets/output-template.md](assets/output-template.md)
   from the manifest; every drafted/stale answer carries its citation; routed questions show
   the reason and owner with no drafted text.
4. **Compile open items** — everything not `drafted` (stale, data-gap, unapproved-source,
   unsupported) plus outstanding approvals becomes an explicit open item routed to a named
   owner. Do not silently drop, guess, or fabricate.
5. **Mark draft & hand off** — set `draft_status: draft-assembled`, record that human approval
   is required before delivery, and route to `communications-compliance-reviewer` and the
   content owners. Never certify, approve, or send.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py) after.
The output check enforces: all required template sections present; every drafted/stale answer
carries a citation **and** is drawn from an approved source (no unsupported/unapproved claims);
routed questions carry no drafted text (fabrication guard); the standard performance disclosure
is present when data is cited; approvals recorded with role, date, and citation; no
delivery/submission, performance-guarantee, or completeness/overclaim language; `draft_status`
is `draft-assembled` and delivery approval is flagged as required; standing note present. Fail
closed on any miss.

## Human approval
`external-delivery`. This skill produces a **draft** response for internal review. Content
owners must approve the content, compliance must clear disclosures and claims, and a human must
approve before the response is sent, submitted, or relied on externally. Content approval,
compliance review, and delivery are separate, human-owned steps — this skill neither performs
nor pre-empts them.

## Failure handling
- **No approved answer for a question** → status `unsupported`; routed to a content owner;
  never fabricated. Ambiguous (two+ approved answers for a topic) is also `unsupported` so the
  owner selects one and the response stays consistent.
- **Only non-approved content matches** → status `unapproved-source`; routed for approval; no
  drafted text.
- **Stale content** (past its `expires` vs `as_of_date`) → status `stale`; drafted but flagged
  as an open item for refresh; still cited.
- **Missing / stale required data point** → status `data-gap`; routed to the data owner; no
  figure fabricated.
- **Missing required approval** → captured as outstanding + an open item; never assumed granted.
- **Unresolvable data / tool timeout** → return the partial draft with an explicit incomplete
  flag and the open-items list; no retry assumption, no guessing.

## Output contract
See [references/controls.md](references/controls.md) and
[assets/output-template.md](assets/output-template.md).
1. **Rendered response** — the template sections (response summary, respondent profile,
   responses, data appendix, disclosures, approvals, open items, source index) populated with
   cited content; routed questions shown with reason + owner and no drafted text.
2. **Machine-readable manifest** — `questionnaire_id`, per-question status + owner + citations,
   disclosures, approvals (recorded/outstanding), open items, source index, `draft_status`
   (`draft-assembled`), and `human_approval_required_before_delivery: true`.
3. **Open-items list** — every unsupported/stale/data-gap/unapproved/outstanding item with its
   routing owner and required human action.
4. **Standing note** — "Draft DDQ/RFP response for human review only. Every answer is drawn from
   approved content and cited; no answer is fabricated. Content owners and compliance must
   review and approve before any answer is sent or submitted to a client, investor, or
   consultant."

## Privacy and records
**Highly Confidential — MNPI / client-confidential.** DDQ content and prospect identity may be
material and non-public; mask client/prospect identifiers to what the response requires, and do
not expose non-public holdings or unpublished performance beyond the approved figures. Retain
the response manifest, citations, and content/config/template versions per the firm's
marketing-and-RFP recordkeeping policy (including SEC marketing-rule books-and-records where
applicable). Log the drafter identity on every read and draft. Data stays within the
deployment's residency boundary.

## Gotchas
- **Drafting ≠ authoring.** The skill reuses **approved** answers; a question with no approved,
  in-date source is an open item routed to the owner, never a freshly invented answer.
- **Approved-source gate beats freshness.** `draft`/`in-review`/`expired` content is never
  drafted from, regardless of dates — it is an unapproved-source open item.
- **Stale looks current — flag it.** Expired content is drafted-but-flagged so a reviewer sees
  the wording and its expiry side by side; it is not passed off as current.
- **No fabricated figures.** A missing or stale required data point is a data-gap routed to the
  data owner, never filled with a plausible number.
- **No promises.** Never add performance/return guarantees, "will outperform", or any claim not
  present in the approved source — the marketing rule and this skill both forbid it.
- **Draft ≠ sent.** Content approval, compliance review, and delivery are separate, human-owned
  steps; the skill records approvals but never grants them and never sends.
- **Versioned contracts.** Record the content-library, disclosure-register, and template
  versions on the manifest so the draft is reproducible and reviewable.
