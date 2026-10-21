# Domain Rules — coverage-meeting-preparer

Orientation references: firm information-barrier / control-room policy, Research independence
and communications standards, and coverage/relationship-management standards. The firm's
approved brief template and approved-source list take precedence and are **versioned contracts**
(`config_version`). These rules are deterministic; the mapping is configuration, not judgment.

## Meeting types

| Type | Meaning |
| ---- | ------- |
| `client` | Existing coverage relationship (mandate history, ongoing dialogue) |
| `prospect` | Target not yet a client (introductory or pitch-oriented) |

## Required content (else `needs-data`)

A brief is only assembled when all of the following are present; otherwise it is
`needs-data` with the missing items listed (never invented):

- `objective` — the meeting objective;
- `developments` — at least one recent company/market development;
- `client_objectives` — at least one hypothesis of what the counterparty wants;
- `discussion_questions` — at least one question to take into the room.

## Developments: dedup and ordering

- Developments are **deduplicated** on `(date, normalized headline)` — first occurrence kept.
- Kept developments are **sorted by date descending** (most recent first), ties broken by `id`.
- The count of removed duplicates is recorded (`developments_deduped`) for transparency.

## Source integrity (else `unsupported-claims`)

Every content item — the objective, the relationship summary, and each development, strategic
issue, client objective, discussion question, and follow-up — must cite a `source_id` that is
(a) present in the brief's `sources[]` inventory and (b) whose `system` is on the approved list.
A claim failing either test is **unsupported** and blocks packaging. Approved systems (default):
`crm`, `filings`, `transcript`, `research`, `marketdata`, `news`, `dataroom`, `comps`.

## Freshness (else `stale-source`)

A cited source older than `freshness_days` (default 45) relative to `as_of_date`, and not
acknowledged (`stale_ack: true`), is **stale** and blocks packaging. Acknowledge deliberately
historical context explicitly; never present stale context as current.

## MNPI / information barrier (else `barrier-hold`)

- A source with `classification: "mnpi"`, a content item flagged `mnpi: true`, or a
  `relationship.mnpi: true` marks the record as containing **private-side / MNPI** material.
- Every MNPI claim is rendered **internal-only** and never placed in a shareable field.
- If any MNPI is present, `control_room_clearance` must be **recorded as approved**; otherwise
  the record is held `barrier-hold` and not packaged.

## Status precedence

`needs-data` → `unsupported-claims` → `stale-source` → `barrier-hold` → `draft-brief`. The
first failing gate determines the status; only a record that clears all gates becomes
`draft-brief` (packageable).

## Required approvals (recorded, not performed by this skill)

| Approval | When required | Recorded value |
| -------- | ------------- | -------------- |
| `supervisory_review` | Always | `approved` before the draft is relied on |
| `control_room_clearance` | When MNPI is present | `approved` before the draft is relied on |
| `external_delivery_approval` | Before any external delivery | slot recorded; **never** `sent`/`delivered` here |

## Hard boundaries (fail closed)

- No **send / distribute / file / post / execute** — draft only; a human delivers.
- No **investment recommendation, price target, valuation opinion, rating**, or investment/
  legal/tax advice.
- No **unsupported / fabricated** content; every line cites an approved in-inventory source.
- No **MNPI in a shareable field** and no externalization without recorded control-room
  clearance.
- No **auto-merge** of an ambiguous client identity.

## Brief — required contents

Durable `engagement_id`; meeting snapshot (objective + attendees); relationship history
(coverage since, last meeting, mandates, open items); deduped/date-sorted developments;
strategic issues; the counterparty's likely objectives (framed as hypotheses to test);
discussion questions; follow-ups; a handling label; a citations index; the required-approvals
block; `reviewer_signoff_required: true`; and the standing note.
