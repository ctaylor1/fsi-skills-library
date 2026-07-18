---
name: customer-interaction-summarizer
description: >-
  Summarize a single customer interaction — call, chat, email, or thread — into a clear,
  source-linked recap: what happened, overall sentiment, commitments made, required
  disclosures given, and open actions, each linked to the underlying transcript segment.
  Use when a contact-center agent or relationship manager asks to "summarize this
  call/chat/email", "what did we promise the customer", "what are the open actions",
  "recap this interaction", or wants a wrap-up / after-call note from a transcript or case
  log. This skill is informational only: it records what was said with citations; it never
  gives advice or a next-best-action, never decides whether a complaint is justified, and
  never makes a coverage, eligibility, vulnerability, fraud, or compliance determination —
  route those to the appropriate adjacent skill.
license: MIT
compatibility: Amazon Quick Desktop; requires contact-center (CCaaS) transcript, CRM/case-management, complaint-system, and approved-knowledge/product-terms MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Customer Service & Experience"
  aws-fsi-skill-type: "Guidance or domain-expertise skills"
  aws-fsi-risk-tier: "R1"
  aws-fsi-archetype: "Explain & summarize"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 1 - low-risk productivity"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Customer Service & Experience"
  aws-fsi-primary-user: "Contact-center agent / relationship manager"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Customer Interaction Summarizer

## Purpose and outcome
Produce a faithful, plain-language recap of one customer interaction so an agent or
relationship manager can see, at a glance, what happened and what still needs doing. A
successful output states the overall sentiment, lists the commitments the parties made, the
required disclosures that were given, the open actions that remain, and the key points —
**every item traceable to a specific transcript segment** — **without** any advice,
next-best-action, or determination about the customer, the complaint, or the case.

## Use when
- "Summarize this call/chat/email", "recap this interaction", "give me a wrap-up note".
- "What did we promise the customer", "what commitments were made", "what are the open
  actions/follow-ups from this contact".
- "Was the recording/consent disclosure given", "what disclosures were read".
- An agent attaches a call transcript, chat log, or email thread and wants a readable
  after-call summary (delivery to the customer or a system of record requires human review
  — see Human approval).

## Do not use
- The user wants the **next best action**, an offer, a save/retention play, or advice on
  what to do next → route to `next-best-action-assistant`; do not answer it here.
- The user asks whether a **complaint is justified / should be upheld**, or wants a
  resolution drafted → `complaint-resolution-assistant`.
- The user asks whether the agent was **compliant / met QA** on the interaction →
  `call-quality-compliance-reviewer`.
- The user asks whether the customer is **vulnerable** or needs special support →
  `vulnerable-customer-support-assistant`.
- The user wants a **goodwill / service-recovery** gesture decided or drafted →
  `service-recovery-assistant`.
- The user wants to **answer the customer's question** from the knowledge base →
  `knowledge-answer-composer`.
- The user wants to **act** on the case (send, refund, escalate, close) → not supported
  here; the R4 `omnichannel-case-orchestrator` handles gated actions.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). In short: this skill is the
**upstream** recap for `next-best-action-assistant`, `complaint-resolution-assistant`,
`call-quality-compliance-reviewer`, `vulnerable-customer-support-assistant`, and
`service-recovery-assistant`. It hands off a normalized summary object + a durable
`summary_id`; it never performs the downstream advice, determination, or action itself.

## Inputs and prerequisites
- Authoritative record of **one interaction at a time**: channel (call/chat/email/thread),
  interaction date, and an ordered list of segments — each with a speaker, text, and a
  citable `ref`. See the input schema in
  [scripts/validate_input.py](scripts/validate_input.py).
- The **interaction date** and channel for the whole record. Reject a file that mixes
  multiple `interaction_id`s unless the user confirms which single interaction to summarize
  (do not silently merge threads).
- Read permission to the transcript/case source. Customer identifiers must arrive
  **masked** (last 4); if raw identifiers appear, they are flagged and not echoed.

## Source hierarchy
Rank sources and cite every item. See [references/source-map.md](references/source-map.md).
1. Contact-center (CCaaS) **recording/transcript of record** for calls, chats, and IVR
   (highest).
2. **CRM / case-management** interaction log and email system of record for threads/notes.
3. **Complaint-management system** for logged complaints and recorded commitments.
4. **Approved knowledge / product terms** — only to explain a term the customer or agent
   used, never to add facts the interaction did not contain.
Never substitute a user assertion for the transcript of record; if they conflict, surface
the conflict and cite both.

## Workflow
1. **Identify scope** — confirm the single interaction (one `interaction_id`), channel, and
   date. If multiple interactions are present, ask which one (do not merge threads).
2. **Normalize** — map each segment to the schema; attach the source citation
   (system + segment/timestamp `ref`) to every extracted item. Run
   [scripts/validate_input.py](scripts/validate_input.py) to confirm structure, single
   interaction, and citable segments, and to surface data-quality gaps (inaudible/redacted
   segments, unmasked identifiers, missing timestamps).
3. **Extract (descriptive only)** — pull key points, **commitments** (who committed to
   what, attributed and cited), **disclosures** given (e.g., recording/consent notice),
   and **open actions**; label overall sentiment from the allowed set
   (positive/neutral/negative/mixed). Record each item verbatim-in-substance and cite it.
   Do not infer facts, promises, or outcomes that were not stated.
4. **Write the summary** — lead with a one-paragraph recap; then the sentiment,
   commitments, disclosures, and open actions as neutral records of what was said, not
   judgments about whether they were right or what to do next.
5. **Surface gaps** — inaudible/redacted segments, unresolved identities, and anything the
   transcript did not cover are listed explicitly in **Data gaps** rather than guessed.
6. **Validate** — run [scripts/validate_output.py](scripts/validate_output.py) before
   presenting or handing off.

## Validation loop
Run `validate_input` before summarizing and `validate_output` after. If an item lacks a
citation, the sentiment label is out of range, a customer identifier is unmasked, or the
output contains advice / next-best-action / determination language, **fix or fail closed** —
do not deliver an uncited or advice/determination-tainted summary.

## Human approval
None required for the agent's own internal read. **Human review is required before the
summary is delivered to the customer, pasted into a system of record, or attached to a
case** — `aws-fsi-human-approval: external-delivery`. The summary is a draft recap for a
human to verify against the record, not an authoritative case note on its own.

## Failure handling
- **Inaudible / redacted / low-confidence segments** → summarize what is legible, list the
  rest under Data gaps; never invent the missing content.
- **Ambiguous or unmasked identity** → flag it, do not echo raw identifiers, and proceed
  only with a masked reference.
- **Multiple interactions in one file** → stop and ask which single interaction; do not
  merge threads, dates, or channels.
- **Source conflict** (transcript vs. user assertion) → present both with citations; do not
  pick a winner.
- **Tool timeout / permission denial** → report partial results and the exact gap; no retry
  assumption.

## Output contract
1. **Header** — masked customer reference, `interaction_id`, channel, interaction date, and
   overall sentiment.
2. **Recap** — one plain-language paragraph of what happened.
3. **Commitments** — each attributed to a party, with owner and citation.
4. **Disclosures** — required notices given, with citation.
5. **Open actions** — outstanding follow-ups, with owner and citation.
6. **Key points & Data gaps** — cited highlights plus an explicit gaps list.
7. **Machine-readable** — the normalized summary object, tagged with a durable `summary_id`
   for downstream skills.
8. **Standing disclaimer** — "Informational summary only; not advice and not a
   determination. Commitments and disclosures are recorded as stated in the interaction and
   must be verified against the system of record."
Every item carries a source citation. See [references/controls.md](references/controls.md).

## Privacy and records
Customer NPI/PII. Mask customer identifiers (show last 4); never echo raw account, card,
phone, or government-ID numbers. Do not transmit interaction content outside the approved
environment. Retain the summary and its citations per records policy; log the read and any
external-delivery approval (who/when). See [references/controls.md](references/controls.md).

## Gotchas
- **Recording a commitment is not making one**: "the agent said the fee would be waived"
  (attributed, cited) is in scope; the assistant promising a waiver is not.
- **Summarize, don't adjudicate**: describing that a customer disputed a fee is in scope;
  saying the complaint "is justified" or "should be upheld" is a determination and is out
  of scope.
- **No next-best-action**: listing open actions the parties already agreed to is in scope;
  proposing new actions, offers, or saves is advice — route it out.
- **Sentiment is a label, not a diagnosis**: use the fixed set; do not infer a customer is
  "vulnerable", "angry enough to churn", or "a fraud risk".
- **One interaction at a time**: do not stitch a call, a follow-up chat, and three emails
  into one recap unless the user explicitly asks and confirms the scope.
- **Keep identifiers masked**: a raw 9- or 10-digit number in the output is a privacy
  failure even if it was in the transcript.
