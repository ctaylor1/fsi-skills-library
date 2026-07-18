# Adjacent-Skill Handoffs — meeting-action-tracker

This skill is **extraction-and-drafting** only. It reads a meeting record, structures the
actions/decisions, and drafts recap + reminder text for a human to confirm and send. It does
not summarize into narrative minutes, compose polished stakeholder comms, send anything, or
write a tracker. Those are separate activities with distinct entitlements and systems of record.

## Upstream (feeds this skill)

| Upstream source / skill | Provides | Handoff artifact |
| ----------------------- | -------- | ---------------- |
| Meeting transcript / recording source | The transcript segments and speakers | `meeting_id`, `segments[]` |
| Calendar invite / meeting record | The attendee roster | roster names for owner resolution |
| Project-tracking system (read-only) | Existing tasks for duplicate detection | `possible-duplicate` links |
| Controlled template library | Approved recap/reminder template | `template_version` |

## Adjacent — do NOT use this skill for (route instead)

| If the request is… | Route to |
| ------------------ | -------- |
| A narrative summary / plain-language minutes of the meeting (no action extraction) | `customer-interaction-summarizer` |
| A polished leadership or stakeholder update assembled from many inputs | `board-committee-pack-builder` |
| Actually creating/assigning/closing tasks or **sending** the messages | `project-tracker-updater` (approval-gated, human) |
| Personalized investment/legal/tax advice or a binding decision | The accountable owner / a specialist skill |

## Downstream (human, not a skill)

The reviewed package is confirmed and acted on by a **human**: they confirm owners and due
dates, send the recap/reminders, and update the tracker (optionally via
`project-tracker-updater`, which is approval-gated). This skill emits a `meeting_id`-keyed
register plus draft comms with `approval_required: true`; it must not perform any of those acts.

## Duplicate-execution prevention

- This skill **does not** send, schedule, or write — those belong to the routes above or to a
  human.
- The package carries `meeting_id` and `template_version` so a reviewer works one authored
  register rather than re-extracting.
- A `possible-duplicate`, `blocked`, `needs-confirmation`, or `unsupported` item is resolved by
  a human (confirm the owner/date, obtain a source, fix the dependency), never force-committed.
