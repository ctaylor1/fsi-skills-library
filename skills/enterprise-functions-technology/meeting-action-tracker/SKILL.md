---
name: meeting-action-tracker
description: >-
  Turn a meeting transcript or notes into a structured, source-cited action package: extract
  decisions, action items with owners and due dates, cross-item dependencies, open questions,
  and risks, then draft a recap and per-owner reminder text from an approved template. Use when
  a project manager or meeting owner needs to capture "who owns what by when", turn meeting
  minutes into trackable actions, prepare a follow-up recap or reminder, or reconcile action
  items against an existing task list. Keywords: meeting action items, follow-ups, decisions,
  owners, due dates, dependencies, open questions, recap, minutes, standup notes, transcript.
  This skill NEVER creates, updates, assigns, or closes tasks in any tracker, NEVER sends email,
  chat, or calendar invites, NEVER changes any system of record, and NEVER asserts an action,
  owner, or due date that is not grounded in the meeting record — it drafts for human review and
  every item and message must be confirmed and delivered by a person.
license: MIT
compatibility: Amazon Quick Desktop; requires meeting transcript/recording, email/calendar, project-tracking, knowledge-base, and controlled-template MCP integrations (all read-only; task creation, messaging, and calendar changes are out of scope and performed by a human).
metadata:
  aws-fsi-category: "Enterprise Functions & Technology"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R1"
  aws-fsi-archetype: "Draft & package"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 1 - low-risk productivity"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Confidential"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Enterprise Functions & Technology"
  aws-fsi-primary-user: "Project manager / meeting owner"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Meeting Action Tracker

## Purpose and outcome
Turn a meeting transcript or notes into an audit-ready **action package**: extract the
decisions, the action items (each with an owner and a due date), the dependencies between
items, the open questions, and the risks — every one tied back to the spot in the record
where it was said — then draft a recap and per-owner reminder text from an approved template.
The outcome is a structured register plus review-ready draft messages (or a clear, itemized
list of what still needs confirmation). A human confirms owners and dates, and a human sends
the messages and updates the tracker. The skill extracts and drafts; it never commits, sends,
or writes anything.

## Use when
- "Pull the action items and decisions out of this meeting / transcript / standup notes."
- "Who owns what by when from today's call, and what's blocked on what?"
- "Draft a recap and reminders for the owners from these minutes."
- "Reconcile these action items against our existing task list before I update the tracker."

## Do not use
- **Narrative minutes / a plain-language summary** of the meeting (no action extraction) →
  `customer-interaction-summarizer`.
- **Composing a polished stakeholder or leadership update** from many inputs →
  `board-committee-pack-builder`.
- **Actually creating, assigning, or closing tasks** in Jira/Asana/Linear or **sending** the
  messages → `project-tracker-updater` (approval-gated), performed by a human.
- **Personalized investment, legal, or tax advice**, or any binding decision on someone's
  behalf → out of scope; refuse and route to the accountable owner.
- Any request to **update a system, send a message, or schedule an invite** → refuse; this
  skill drafts only.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill is extraction-and-drafting
only. It consumes the meeting record (and, read-only, an existing task list for dedup) and
emits a `meeting_id`-keyed action register plus draft comms with `approval_required: true`.
Sending messages and writing the tracker belong to a human via `project-tracker-updater`;
narrative minutes and polished stakeholder comms route to the skills above.

## Inputs and prerequisites
- The meeting record: `meeting_id`, title, date, attendee roster, and either a transcript
  (`segments[]` with speaker + locator) or structured notes; the extracted `candidate_items[]`
  (type, text, proposed owner, proposed due date, `depends_on`, `source_segments`); optionally
  an existing task list for duplicate detection. Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Read access to the transcript/recording source, email/calendar (context only),
  project-tracking (read-only, for dedup), and the controlled recap/reminder template.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The meeting record (transcript or
signed-off notes) is authoritative for what was said, decided, and committed; the attendee
roster resolves owners; the existing task list is read-only context for dedup only. Cite every
item back to a `segment_id`. The recap/reminder template is a **versioned contract**
(`template_version`) — record the version on every package.

## Workflow
1. **Validate & normalize** — run `validate_input`; confirm the meeting, roster, and candidate
   items are structurally complete; flag items with no source, no owner, or a bad due date.
2. **Build the register (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): resolve each owner
   against the roster, normalize due dates, resolve `depends_on` (missing reference or cycle),
   require a citation, and assign a status. Rules:
   [references/domain-rules.md](references/domain-rules.md).
3. **Assign status** — `unsupported` (no citation), `blocked` (dependency missing/cyclic), or
   `needs-confirmation` (owner unresolved or due unconfirmed) each keep an item **out** of the
   committed register; only a sourced, owner-resolved, date-confirmed item becomes `ready`.
4. **Draft the package** — from [assets/output-template.md](assets/output-template.md):
   decision log, action register (ready items), open questions/risks, a follow-ups list (what
   needs confirmation), and draft recap + per-owner reminder text. Every message carries
   `approval_required: true` and is a draft — nothing is addressed, sent, or scheduled.
5. **Validate output** — run [scripts/validate_output.py](scripts/validate_output.py); fail
   closed on any miss.
6. **Never act** — hand the reviewed package to a human to confirm, send, and update the tracker.

## Validation loop
Run `validate_input` before and `validate_output` after. The output screen enforces: every
register/decision/open item is cited (no unsupported assertion); a `ready` item is owner-
resolved and date-confirmed; every draft message is `delivery: draft` with `approval_required`
and no "sent/created/scheduled/updated the tracker" language; no personalized investment/legal/
tax advice; standing disclaimer present. See [references/controls.md](references/controls.md).
Correct and re-run until it passes or the item is flagged not-ready.

## Human approval
`external-delivery`. A human must confirm owners and due dates, send any message, and make any
tracker/calendar change before anything leaves this skill or a system of record changes. This
skill proposes and drafts; it never sends, schedules, assigns, or writes. Internal drafting may
be reviewer-sampled per [references/controls.md](references/controls.md).

## Failure handling
- **No source segment** → `unsupported`; the item is listed as needs-source, never placed in
  the committed register on a guess.
- **Owner not on the roster / missing** → `needs-confirmation`; name the unresolved owner; do
  not assign a person who was not in the meeting.
- **Due date missing, tentative, or non-ISO** → `needs-confirmation`; surface it for the owner
  to confirm; never invent a deadline.
- **Dependency references an unknown item or forms a cycle** → `blocked`; a human resolves the
  ordering; never drop or reorder silently.
- **Possible duplicate of an existing task** → link as `possible-duplicate` for human review;
  never merge or close.
- **Tool timeout / partial transcript** → return partial output with an explicit incomplete
  flag and the `template_version` used; no retry assumption.

## Output contract
1. **Register queue** — per item: `item_id`, type, one-line text, owner (or "unresolved"),
   due date (or "unconfirmed"), status, and citation.
2. **Action package** (from the template) — decision log, action register (ready items),
   open questions/risks, follow-ups (needs-confirmation/blocked/unsupported, itemized), and
   draft recap + per-owner reminder text, each `approval_required: true`.
3. **Follow-ups list** — every not-ready item with exactly what is missing.
4. **Machine-readable** — the register keyed by `meeting_id` with `template_version`.
5. **Standing note** — "Draft meeting outputs for human review only; this skill does not create
   tasks, send messages, or change any tracker, calendar, or system of record, and every action,
   owner, and due date must be confirmed before it is treated as committed."

## Privacy and records
**Confidential.** Meeting content may include personnel, commercial, or customer-sensitive
detail — include only what a follow-up needs (data minimization) and do not copy the full
transcript into the package. Keep owner names to attendees on the roster. Retain the register,
the `template_version`, and citations with the meeting record; log every read and every package
produced with the author identity. Do not place meeting content in URLs or send it anywhere the
user did not direct.

## Gotchas
- **Drafting ≠ doing.** The register and messages are drafts; a human confirms, sends, and
  updates the tracker. Never emit "created/assigned/sent/scheduled/updated" language or imply a
  system changed.
- **Every item needs a citation.** An action, decision, or due date with no `source_segment` is
  an unsupported assertion and is kept out of the committed register.
- **Owners are attendees, not guesses.** Resolve owners against the roster; an unresolved or
  absent owner is `needs-confirmation`, never auto-assigned.
- **Dates are confirmed, not inferred.** "Sometime next week" is not a due date; it stays
  `needs-confirmation` until the owner confirms.
- **Dependencies can lie.** A `depends_on` pointing at a missing item, or a cycle, blocks the
  item; surface it rather than reorder silently.
- **Template is a versioned contract.** Record `template_version` on every package so the recap
  and reminder wording are reproducible and reviewable.
