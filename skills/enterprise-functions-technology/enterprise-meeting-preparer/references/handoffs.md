# Adjacent-Skill Handoffs — enterprise-meeting-preparer

This skill is **prep-time drafting only**. It assembles a source-cited pre-read for a human
to review and, if they choose, distribute. It does not schedule, send, summarize after the
fact, review contracts, research external parties, or write tasks — those are separate
activities with distinct entitlements and systems of record.

## Upstream (feeds this skill)

| Upstream source / skill | Provides | Handoff artifact |
| ----------------------- | -------- | ---------------- |
| Calendar / email | The meeting event and attendee list | `meeting_id`, datetime, organizer, attendees |
| Documents / files & contracts | Background pre-reads and contract/PO context | document/contract refs with dates |
| Knowledge base | Prior background and project material | `kb:page` refs |
| Project tracking | Prior decisions, open risks, outstanding actions | `tracker:decision/risk/action` refs |

## Adjacent — do NOT use this skill for (route instead)

| If the request is… | Route to |
| ------------------ | -------- |
| Summarizing what happened / meeting minutes / a recap **after** the meeting, or the decisions and actions that came out of it | `meeting-action-tracker` |
| Drafting or sending the follow-up or distribution **email** | an authorized human (out of scope; this skill never sends) |
| Reviewing or interpreting a **contract** clause-by-clause | `contract-obligation-extractor` |
| Researching an **external** party, prospect, client, or competitor | `stakeholder-account-researcher` |
| Creating or updating **tasks / action items** in the tracker | `task-tracker-updater` |
| Scheduling, rescheduling, or sending the **invite** | a human via the calendar system |

## Downstream (human, not a skill)

The reviewed and approved brief is distributed by an **authorized human**, who also drafts
and sends any distribution or follow-up email. This skill emits a `meeting_id`-keyed draft
brief plus a `reviewer_signoff_required` flag; it must not perform the distribution or any
calendar/tracker write.

## Duplicate-execution prevention

- This skill **does not** schedule, send, summarize post-meeting, review contracts, research
  external parties, or write tasks — those belong to the routes above or to a human.
- A brief carries the `meeting_id` and `as_of_date` so a reviewer works one authored draft
  rather than re-assembling.
- A `needs-data`, `unresolved-attendee`, `unsupported-content`, or `stale-source` record is
  resolved by a human (supply data, confirm identity, substantiate, or refresh), never
  force-packaged.
