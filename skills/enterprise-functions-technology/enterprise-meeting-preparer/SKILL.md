---
name: enterprise-meeting-preparer
description: >-
  Assemble an internal meeting brief (prep pack) from approved sources: the calendar event,
  attendees and roles, agenda, relevant documents and contracts, prior decisions, open risks,
  and outstanding action items, drafted as a concise, fully source-cited brief from an
  approved template. Use when an executive, manager, or knowledge worker needs to prepare for
  or get briefed on an internal meeting, build a pre-read or prep pack, pull together
  background, stakeholders, decisions, risks, and prior actions, or produce talking points
  ahead of a 1:1, staff, steering, or review meeting. Keywords: meeting brief, meeting prep,
  pre-read, agenda, briefing pack, stakeholders, action items, decisions, talking points.
  This skill NEVER schedules, sends, distributes, or updates a meeting, invite, calendar, or
  brief; never makes, approves, or authorizes any decision or commitment; never gives
  investment, legal, or tax advice; and never states anything not backed by a cited source —
  it drafts a brief for human review.
license: MIT
compatibility: Amazon Quick Desktop; requires calendar/email, document/file, contracts/procurement, knowledge-base, and project-tracking MCP integrations (all read-only; drafting only — no send, schedule, or distribute).
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
  aws-fsi-primary-user: "Executive / manager / knowledge worker"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Enterprise Meeting Preparer

## Purpose and outcome
Turn a scheduled internal meeting and its approved context into an audit-ready **meeting
brief (prep pack)**: identify the event, attendees and roles, agenda, relevant documents and
contracts, prior decisions, open risks, and outstanding action items, then draft a concise,
**fully source-cited** brief from an approved template. The outcome is a review-ready
pre-read (or a clear, itemized reason it cannot be assembled yet) that a human reads,
verifies, and — if they choose — distributes. The skill never schedules or sends anything,
never decides or commits on anyone's behalf, and states nothing that a cited source does not
support.

## Use when
- "Prepare me for / brief me on the steering meeting on Thursday."
- "Build a pre-read / prep pack for the Q3 budget review."
- "Pull the background, stakeholders, decisions, and open actions for this 1:1."
- "What are the talking points and prior action items going into this staff meeting?"

## Do not use
- **Post-meeting** minutes, notes, recap, or the decisions/actions that came out of it →
  `meeting-action-tracker`.
- **Drafting or sending** the follow-up or distribution email → an authorized human drafts
  and sends it (out of scope here; this skill never sends).
- **Interpreting or reviewing a contract** clause-by-clause → `contract-obligation-extractor`.
- **External party / account research** (prospect, client, competitor intelligence) →
  `stakeholder-account-researcher`.
- **Creating or updating tasks** in the project tracker → `task-tracker-updater` (a write
  action, out of scope here).
- Any request to **schedule/send/distribute, decide, approve, commit, or advise** → refuse;
  draft only and route to a human.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill is **prep-time drafting
only**. It consumes read-only context from calendar/email, files/contracts, the knowledge
base, and the project tracker, and emits a `meeting_id`-keyed brief with
`reviewer_signoff_required`. Sending, scheduling, post-meeting summarization, contract
review, external research, and task writes belong to the routes above or to an authorized
human.

## Inputs and prerequisites
- The meeting record: `meeting_id`, `title`, `datetime`, `purpose`, organizer, location, and
  the attendee list (name, role, internal/external, resolved); the agenda items, prior
  decisions, open risks, and prior action items; optional narrative talking points. Every
  content item cites a `source_id` from the meeting's approved **source inventory**. Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- An `as_of_date` (drives freshness and overdue-action calculations) and a `freshness_days`
  threshold.
- Read access to calendar/email, documents/contracts, the knowledge base, and the project
  tracker. No write, send, or schedule capability is used.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The calendar/email system is the
system of record for the event and attendees; files/contracts and the knowledge base supply
background; the project tracker supplies decisions, risks, and action items. **Cite every
item** with `{system}:{ref}@{date}`. Nothing enters the brief without a source; the approved
brief template is a **versioned contract**.

## Workflow
1. **Validate & normalize** — run `validate_input`; confirm each meeting is structurally
   complete and every content item cites a source in the inventory; flag gaps as warnings.
2. **Assemble deterministically** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): resolve attendees,
   check content-to-source integrity, screen source freshness against `freshness_days`, flag
   overdue prior actions, and assign a status. Rules:
   [references/domain-rules.md](references/domain-rules.md).
3. **Assign status** — `needs-data`, `unresolved-attendee`, `unsupported-content`, or
   `stale-source` blocks assembly with an itemized reason; only a clean record becomes
   `draft-brief`.
4. **Draft the brief** — for a packageable meeting, assemble the brief from
   [assets/output-template.md](assets/output-template.md): identifiers, purpose, attendees,
   agenda, decisions, risks, open/overdue actions, talking points, citations, and the
   reviewer sign-off block. No statement without a cited source.
5. **Validate output** — run [scripts/validate_output.py](scripts/validate_output.py); fail
   closed on any miss (template fidelity, unsupported content, scheduling/decision/advice
   language, standing disclaimer).
6. **Never send** — hand the reviewed draft to the human, who verifies and distributes.

## Validation loop
Run `validate_input` before and `validate_output` after. The output screen enforces:
template fidelity (required sections, no unfilled placeholders); a packageable record is
attendee-resolved, fully source-cited, and free of blocking stale sources; no scheduling/
sending, decision/commitment, outcome-guarantee, or investment/legal/tax-advice language;
standing disclaimer present. See [references/controls.md](references/controls.md). Correct
and re-run until it passes or the record is flagged not-packageable.

## Human approval
`external-delivery`. A human must review and authorize before the brief is distributed or any
system of record (calendar, tracker, mailbox) is changed. This skill proposes and drafts; it
never schedules, sends, decides, approves, or advises. Internal drafting may be
reviewer-sampled per [references/controls.md](references/controls.md).

## Failure handling
- **Missing required input** (no purpose, attendees, or agenda) → `needs-data`; list exactly
  what is missing; do not invent an agenda or attendee.
- **Unresolved attendee** → `unresolved-attendee`; a human confirms who is in the room; never
  guess an identity or role.
- **Content cites an unknown source** → `unsupported-content`; drop or substantiate the item;
  never fabricate a fact, decision, or figure to fill the brief.
- **Stale source** (older than `freshness_days`, not acknowledged) → `stale-source`; refresh
  it or acknowledge it explicitly; never silently present stale context as current.
- **Tool timeout / partial context** → return partial output with an explicit incomplete flag
  and the sources used; no retry assumption.

## Output contract
1. **Prep queue** — per meeting: `meeting_id`, title, status, `packageable`, and a one-line
   reason.
2. **Meeting brief** (per packageable meeting) — identifiers, purpose, attendees, agenda,
   decisions, risks, open/overdue actions, talking points, a citations list, and
   `reviewer_signoff_required: true`, following [assets/output-template.md](assets/output-template.md).
3. **Blocked list** — each non-packageable meeting with its itemized reason(s).
4. **Machine-readable** — the brief records keyed by `meeting_id` with `as_of_date`.
5. **Standing note** — "Internal meeting brief for preparation only; this skill does not
   schedule, send, distribute, or update any meeting, invite, calendar, or system of record,
   does not make or authorize any decision or commitment, and every item must be verified
   against its cited source before the meeting."

## Privacy and records
**Confidential.** Include only the context needed to prepare for the meeting (data
minimization); do not pull unrelated personal or customer data into a brief. Respect the
classification of each source and do not elevate restricted content into a wider-distribution
pre-read. Retain the draft brief, the `as_of_date`, source citations, and the reviewer
sign-off with the meeting record; log every read and every brief produced with the preparer
identity. Distribution is a human action outside this skill.

## Gotchas
- **Drafting ≠ sending.** The brief is a pre-read draft; a human distributes it. Never emit
  "invite sent / calendar updated / brief distributed" language or imply anything was booked.
- **Report decisions; never make them.** The brief may restate a *sourced* prior decision
  ("the committee approved X on <date> [cite]"); it must never approve, authorize, or commit
  on its own.
- **Every line needs a source.** A confident sentence with no citation is unsupported content
  and is stripped by the output screen — no background fact, figure, risk, or action without
  a `source_id`.
- **Freshness matters.** A months-old document presented as current context misleads the
  room; stale sources block unless explicitly acknowledged, and the brief records the
  `as_of_date`.
- **No advice.** Surfacing options and their sourced trade-offs is fine; telling the reader
  what to decide, buy, sell, or sign is investment/legal/tax advice and is prohibited.
- **Overdue actions are flags, not verdicts.** The brief highlights an overdue prior action
  for the room to address; it does not close, reassign, or reschedule it.
