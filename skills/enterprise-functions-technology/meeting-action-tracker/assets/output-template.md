# Meeting Action Package — DRAFT (for human review)

> Draft meeting outputs for human review only; this skill does not create tasks, send
> messages, or change any tracker, calendar, or system of record, and every action, owner, and
> due date must be confirmed before it is treated as committed.

Fill every `{{placeholder}}` from the cited meeting record. Do not add an action, owner, due
date, or decision that is not backed by a listed `seg=` citation. Keep owners to attendees on
the roster.

## 1. Meeting identifiers

| Field | Value |
| ----- | ----- |
| Meeting | {{meeting_id}} — {{title}} |
| Date | {{meeting_date}} |
| Attendees | {{attendees}} |
| Template version | {{template_version}} |
| Prepared as of | {{as_of_date}} |

## 2. Decision log (ready decisions only)

| # | Decision | Decided by | Citation |
| - | -------- | ---------- | -------- |
| {{n}} | {{decision_text}} | {{decided_by}} | {{seg_citation}} |

## 3. Action register (ready actions only)

| # | Action | Owner | Due date | Depends on | Citation |
| - | ------ | ----- | -------- | ---------- | -------- |
| {{n}} | {{action_text}} | {{owner}} | {{due_date}} | {{depends_on}} | {{seg_citation}} |

Every action above is sourced, owner-resolved, and date-confirmed. Nothing here has been
created in a tracker or assigned — a human does that.

## 4. Open questions & risks

| # | Type | Item | Raised by | Citation |
| - | ---- | ---- | --------- | -------- |
| {{n}} | {{open_question|risk}} | {{text}} | {{raised_by}} | {{seg_citation}} |

## 5. Follow-ups (needs confirmation before committing)

| # | Item | Status | What is missing | Citation |
| - | ---- | ------ | --------------- | -------- |
| {{n}} | {{text}} | {{needs-confirmation|blocked|unsupported|possible-duplicate}} | {{gap}} | {{seg_citation_or_none}} |

## 6. Draft recap (not sent — for the owner to review and send)

> Delivery: draft · Approval required: yes

{{recap_body_citing_decisions_and_ready_actions}}

## 7. Draft reminders (one per ready action owner — not sent)

> Delivery: draft · Approval required: yes

- To {{owner}} — re: {{action_text}} (due {{due_date}}). Confirm before this is treated as a
  committed action. Citation: {{seg_citation}}.

## 8. Reviewer sign-off (required before anything is sent or written)

- [ ] Every action, owner, and due date verified against the meeting record.
- [ ] Owners confirmed with the people named; due dates confirmed.
- [ ] Follow-ups resolved or intentionally deferred.
- [ ] Authorized to send the recap/reminders and update the tracker (done by a human).

Reviewer: ________________________  Date: ____________  Decision: send / revise / hold
