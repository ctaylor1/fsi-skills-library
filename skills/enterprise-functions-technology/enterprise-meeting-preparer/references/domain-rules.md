# Domain Rules — enterprise-meeting-preparer

Meeting-brief assembly logic applied by
[../scripts/calculate_or_transform.py](../scripts/calculate_or_transform.py). This reference
governs how raw meeting context becomes a controlled, source-cited brief. It makes no
decisions, gives no advice, and sends nothing; the defaults below are illustrative and are
confirmed against the deployment's brief template and freshness policy.

## Required inputs (per meeting)

| Field | Required | Effect if missing |
| ----- | -------- | ----------------- |
| `meeting_id`, `title`, `datetime` | Structural | Input validation **error** (record is ill-formed) |
| `purpose` | Content | `needs-data` (a brief without a purpose is not assembled) |
| `attendees` (non-empty) | Content | `needs-data` |
| `agenda_items` (non-empty) | Content | `needs-data` |
| `sources` inventory | Content | Any content item without a matching source → `unsupported-content` |

Optional: `decisions`, `risks`, `prior_actions`, `talking_points` — each item cites a
`source_id`.

## Deterministic computations

1. **Attendee resolution.** Every attendee must be `resolved: true` (identity and role
   confirmed against the source of record). Any unresolved attendee → `unresolved-attendee`;
   the room roster is never guessed.
2. **Content-to-source integrity.** Every content item (agenda, decision, risk, prior action,
   talking point) must cite a `source_id` present in the meeting's `sources` inventory. A
   dangling citation → `unsupported-content`; the item is not carried on a guess.
3. **Source freshness.** For each cited source, `age_days = as_of_date − source.date`. A
   source with `age_days > freshness_days` (default 30) is **stale**. A cited stale source
   that is not acknowledged (`stale_ack: true`) → `stale-source`. Acknowledged stale sources
   (intentional historical context) do not block but their age is recorded.
4. **Overdue prior actions.** A prior action with `status: open` and `due_date < as_of_date`
   is flagged `overdue: true` in the brief. This is a **highlight for the room**, never a
   closure, reassignment, or reschedule.
5. **Template fidelity.** A packageable brief is rendered into the approved template with all
   required sections present and no unfilled placeholders; `reviewer_signoff_required: true`.

## Status precedence

`needs-data` → `unresolved-attendee` → `unsupported-content` → `stale-source` →
`draft-brief`. Only `draft-brief` is `packageable`.

## What the rules never do

- No scheduling, sending, distributing, or calendar/tracker writes — the brief is drafted for
  authorized human review and distribution.
- No decision, approval, authorization, or commitment — a *sourced* prior decision may be
  restated, never created.
- No investment/legal/tax advice and no outcome guarantees.
- No fabrication — missing, unresolved, unsupported, or stale context is reported, never
  invented or silently presented as current.
