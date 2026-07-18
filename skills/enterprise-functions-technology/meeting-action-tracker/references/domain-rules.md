# Domain Rules — meeting-action-tracker

Extraction and register logic applied by
[../scripts/calculate_or_transform.py](../scripts/calculate_or_transform.py). All wording and
thresholds are a **versioned contract** (`template_version`); the defaults below are the
starting configuration and must be confirmed with the meeting-operations owner at deployment.
These rules structure and draft — they never send, schedule, write, or decide.

## Item types

| Type | Meaning | Owner required | Due required |
| ---- | ------- | -------------- | ------------ |
| `action` | A committed task someone will do | Yes | Yes |
| `decision` | A choice the meeting made | A cited decision-maker | No |
| `dependency` | An explicit "X waits on Y" link | No | No |
| `open_question` | An unresolved question to follow up | No | No |
| `risk` | A risk/issue raised for tracking | No | No |

## Deterministic transforms

1. **Citation requirement.** Every item must cite at least one `source_segment` present in the
   meeting record. An item with no valid citation → `unsupported`; it is listed as needs-source
   and is **never** placed in the committed register.
2. **Owner resolution.** A proposed owner is resolved against the attendee **roster**
   (case-insensitive, trimmed). Resolved and `owner_confirmed` → eligible; off-roster, missing,
   or unconfirmed → `owner_status: unresolved` / `owner_confirmed: false`. `action` items
   require a resolved, confirmed owner to be `ready`.
3. **Due-date normalization.** A due date is accepted only if it is ISO (`YYYY-MM-DD`) and
   `due_confirmed` is true. A missing, relative, or non-ISO date → `due_confirmed: false`. An
   `action` requires a confirmed ISO due date to be `ready`.
4. **Dependency resolution.** Each `depends_on` id must reference a known item. A reference to a
   missing item, or a dependency cycle, → `dependency_status` is `missing:<id>` or `cycle` and
   the item is `blocked`.
5. **Duplicate detection (read-only).** If an existing task list is supplied, an action whose
   normalized text matches an open task is flagged `possible-duplicate` and linked to that task
   id for human review; it is never merged or closed.

## Status precedence

`unsupported` (no citation) → `blocked` (dependency missing/cyclic) → `needs-confirmation`
(owner unresolved or due unconfirmed) → `possible-duplicate` (matches an existing task) →
`ready`. Only `ready` items enter `action_register` / `decision_log` / `open_questions`;
everything else goes to `follow_ups` with the specific gap named.

## Draft comms (text only)

- **Recap.** A draft summary listing the decisions and ready actions (owner + due), each cited.
  Marked `delivery: draft`, `approval_required: true`. Not addressed, sent, or scheduled.
- **Per-owner reminder.** For each ready action with a resolved owner, a draft reminder naming
  the item and due date, marked `delivery: draft`, `approval_required: true`.
- Draft comms are built only from `ready` items, so nothing unsupported or unconfirmed is ever
  put in front of a recipient.

## What the rules never do

- No task creation/assignment/closure, no message send, no calendar change, no tracker write.
- No fabricated owner or deadline; a gap is reported, never invented.
- No advice and no binding decision on anyone's behalf.
