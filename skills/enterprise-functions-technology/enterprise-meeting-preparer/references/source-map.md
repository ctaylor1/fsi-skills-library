# Source Map — enterprise-meeting-preparer

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Calendar / email** | The meeting event (system of record), datetime, organizer, location, attendee list | Read-only |
| 2 | **Documents / files & contracts / procurement** | Background pre-reads, referenced documents, contract/PO context | Read-only |
| 3 | **Knowledge base** | Prior background, project pages, reference material | Read-only |
| 4 | **Project tracking** | Prior decisions, open risks, and outstanding action items with owners and due dates | Read-only |
| 5 | **Controlled template & content library** | Approved brief template, section order, standing disclaimer | Read-only |

The calendar/email system is authoritative for the event and who is invited. The approved
brief template is a **versioned contract** — record which template version and `as_of_date`
every brief was built from. Never state a fact, decision, risk, or figure that a listed
source does not support.

## Citation format

`{system}:{ref}@{date}` — e.g. `calendar:event=EVT-8801@2026-07-15`,
`files:doc=DOC-330;v=3@2026-07-11`, `tracker:decision=DEC-77@2026-06-30`,
`tracker:action=ACT-12@2026-07-02`, `kb:page=KB-501@2026-07-09`.

## Freshness / effective dates

- Every content item carries the `date` of its source. A source older than `freshness_days`
  (default 30) relative to `as_of_date` is **stale**; if it is cited and not explicitly
  acknowledged (`stale_ack: true`), the meeting is flagged `stale-source` and not packaged.
- Historical-but-intentional context (e.g., a decision made last quarter) is acknowledged
  with `stale_ack: true` on that source so it does not block, while still recording its age.
- The brief always records the `as_of_date` it was assembled against.

## Least-privilege operations (deployment)

- `calendar.get_event(meeting_id)` / `calendar.list_attendees(meeting_id)` — read-only.
- `files.get(doc_id, version)` / `contracts.get(ref)` — read-only, bounded.
- `kb.get(page_id)` — read-only.
- `tracker.get_decisions/risks/actions(project|meeting)` — read-only.
- `templates.get('meeting-brief', version)` — read-only controlled content.

No mutation from this skill. Scheduling, sending, distributing the brief, and writing tasks
or calendar changes are **out of scope** — performed by an authorized human after review.
