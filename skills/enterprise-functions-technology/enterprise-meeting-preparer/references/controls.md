# Controls — enterprise-meeting-preparer

- **Risk tier:** R1 — informational. Source-grounded assembly and summarization; no binding
  decision. **Action mode:** Draft-only; no system-of-record change.
- **Human approval:** `external-delivery` — a human must review and authorize before the
  brief is distributed or any system of record (calendar, tracker, mailbox) is changed.
  Internal drafting may be reviewer-sampled.

## Prohibited (fail closed)

- **Scheduling / sending / distributing / updating** any meeting, invite, calendar, mailbox,
  or the brief itself. This skill drafts only; a human sends.
- **Making, approving, authorizing, or committing** to any decision on anyone's behalf. The
  brief may restate a *sourced* prior decision; it never makes one.
- **Personalized investment, legal, or tax advice**, or telling the reader what to decide,
  buy, sell, or sign.
- **Outcome guarantees** for anything the meeting will decide.
- **Unsupported / fabricated content** — any statement, fact, figure, decision, risk, or
  action not backed by a cited source in the inventory.
- **Elevating restricted content** into a wider-distribution pre-read beyond its
  classification.

## Brief statuses (this skill may set only these)

`draft-brief` (packageable) | `needs-data` | `unresolved-attendee` | `unsupported-content` |
`stale-source`. It may **not** set `scheduled`, `sent`, `distributed`, `approved`, or
`decided`.

## Required output screens (`scripts/validate_output.py`)

- **Template fidelity:** required sections present and no unfilled `{{placeholder}}` tokens.
- A `packageable` record is **attendee-resolved**, **fully source-cited** (no unsupported
  content), and free of **blocking stale sources**, with a non-empty citations list and
  `reviewer_signoff_required: true`.
- No scheduling/sending/distributing language (regex): `invite sent`, `calendar updated`,
  `meeting scheduled`, `brief distributed`, `I have scheduled/sent/booked`, etc.
- No decision/commitment language: `this brief approves`, `hereby authorize`, `we commit to`,
  `you are authorized to proceed`, `the decision is final`, guarantee-of-outcome, etc.
- No investment/legal/tax-advice language.
- Standing note present: the draft-only / no-send / no-decision disclaimer.

## Freshness & sourcing discipline

- Source freshness is measured from each source's `date` against `as_of_date` using
  `freshness_days`. A cited, unacknowledged stale source blocks packaging.
- Every content item (agenda, decision, risk, action, talking point) must cite a `source_id`
  present in the meeting's source inventory; a dangling citation is unsupported content.

## Data classification, privacy, records

- **Confidential.** Data minimization: include only context needed to prepare for the
  meeting; do not pull unrelated personal or customer data into a brief.
- Retain the draft brief, the `as_of_date`, source citations, and the reviewer sign-off with
  the meeting record; log every read and every brief produced with the preparer identity.
- Distribution and any system-of-record change are human actions outside this skill.
