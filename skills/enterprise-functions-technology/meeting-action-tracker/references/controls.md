# Controls — meeting-action-tracker

- **Risk tier:** R1 — informational / drafting support. No binding decision. **Action mode:**
  Draft-only; no system-of-record change.
- **Human approval:** `external-delivery` — a human must confirm owners and due dates, send any
  message, and make any tracker/calendar change before anything leaves this skill or a system
  of record changes. Internal drafting may be reviewer-sampled.

## Prohibited (fail closed)

- **Creating, updating, assigning, reordering, or closing tasks** in any tracker; **sending**
  email/chat; **scheduling** calendar invites; or any other system-of-record change. This skill
  drafts only; a human acts.
- **Unsupported assertions** — any action, decision, owner, or due date not grounded in a cited
  `segment_id` of the meeting record.
- **Fabricated owners or deadlines** — assigning a person not on the roster, or inventing a due
  date the record does not state.
- **Silent changes** — implying (in text or status) that a task, message, invite, or tracker
  entry was created, sent, scheduled, or updated.
- **Personalized investment, legal, or tax advice**, or any binding decision on someone's behalf.

## Item statuses (this skill may set only these)

`ready` (sourced, owner-resolved, date-confirmed — eligible for the committed register) |
`needs-confirmation` (owner unresolved or due unconfirmed) | `blocked` (dependency missing or
cyclic) | `unsupported` (no citation) | `possible-duplicate` (matches an existing task —
linked for human review). It may **not** set `created`, `assigned`, `sent`, `scheduled`,
`done`, `closed`, or `committed`.

## Required output screens (`scripts/validate_output.py`)

- Every register / decision / open item is cited; an item with no citation is `unsupported`
  and must not appear as `ready`/`needs-confirmation`/`blocked` in the committed set.
- A `ready` action is owner-resolved (`owner_status == "resolved"`), `owner_confirmed`,
  `due_confirmed`, and dependency-clean; a `ready` decision names a cited decision-maker.
- Only `ready` items appear in `action_register` / `decision_log` / `open_questions`.
- Every `draft_comms` entry has `delivery == "draft"` and `approval_required == true`.
- No silent system-change language (regex): `created the task`, `added ... in jira/asana/
  linear/monday/trello/clickup`, `sent the reminder/email/message/update`, `posted to
  slack/teams`, `scheduled the meeting/invite`, `updated the tracker/board`, `assigned ... in
  <tracker>`, `marked ... complete/done/closed`.
- No personalized investment/legal/tax advice language.
- Standing note present: the draft-only / no-send / no-write / confirm-before-committed disclaimer.

> Note on wording: the screen targets **claims that the change was already performed** (past
> tense / first person / completed). An action *describing future work* ("Alice to create a
> Jira ticket") is legitimate register content and does not trip the screen; a sentence
> claiming the skill *"created the Jira ticket and sent the reminders"* does.

## Extraction discipline

- Owner resolution is against the **attendee roster**; an off-roster or missing owner is
  `needs-confirmation`, never auto-assigned.
- Due dates are normalized to ISO against a stated `as_of_date`; tentative/relative dates stay
  `needs-confirmation`.
- `depends_on` is resolved against the item set; a missing reference or a cycle → `blocked`.

## Data classification, privacy, records

- **Confidential.** Meeting content may include personnel, commercial, or customer-sensitive
  detail — include only what a follow-up needs (data minimization); do not copy the full
  transcript into the package. Keep owner names to roster attendees.
- Retain the register, the `template_version`, and citations with the meeting record; log every
  read and every package produced with the author identity. Never place meeting content in URLs
  or route it anywhere the user did not direct.
