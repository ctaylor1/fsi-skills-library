# Source Map — meeting-action-tracker

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Meeting record** — transcript / recording summary / signed-off notes (versioned) | What was said, decided, and committed; the `segment_id` locators every item cites | Read-only |
| 2 | **Attendee roster** (from the calendar invite / meeting record) | Resolving a proposed owner to a real participant | Read-only |
| 3 | **Project-tracking system** (Jira/Asana/Linear/etc.) | Read-only duplicate detection against existing tasks; never written here | Read-only |
| 4 | **Email / calendar** | Context only (meeting time, thread references); never sent or scheduled here | Read-only |
| 5 | **Controlled template & content library** | Approved recap/reminder template, standing disclaimer | Read-only |
| 6 | **Knowledge base** | Optional context for a decision reference (linked, not asserted) | Read-only |

The recap/reminder template and the extraction rules are a **versioned contract**
(`template_version`). Never present an item, owner, or due date that the meeting record does
not support; record the version on every package.

## Citation format

`{system}:{ref}@{date/version}` — e.g. `meeting:MTG-2026-07-15;seg=S3`,
`roster:MTG-2026-07-15@2026-07-15`, `tracker:task=PROJ-482@2026-07-15`,
`template:meeting-actions@meeting-actions-2026.07`.

Every extracted action, decision, open question, and risk cites at least one `seg=` locator
in the meeting record. An item with no locator is `unsupported` and is never committed.

## Freshness / effective dates

- The meeting record is read as authored; if only a partial transcript is available the
  package is flagged incomplete and says so.
- Due dates are normalized to ISO (`YYYY-MM-DD`) against a stated `as_of_date`; a tentative or
  relative date ("next week") is **not** a due date and stays `needs-confirmation`.

## Least-privilege operations (deployment)

- `meeting.get(meeting_id)` / `transcript.get(meeting_id)` → segments + roster — read-only.
- `roster.get(meeting_id)` → attendee identities for owner resolution — read-only.
- `tracker.find(query)` → possible-duplicate existing tasks — read-only, bounded.
- `templates.get('meeting-actions', version)` → controlled recap/reminder template — read-only.

No mutation from this skill. Creating or updating tasks, sending messages, and scheduling
invites are **out of scope** — performed by an authorized human (see
`project-tracker-updater`) after review.
