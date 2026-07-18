# Domain Rules — transaction-process-tracker

Orientation: standard M&A / capital-markets deal-process management (outreach → NDA →
data-room access → diligence → bid → approval). The firm's **deal-process standard** and its
**process config** (`stage_order`, `required_approvals`, reminder window) take precedence and
are versioned contracts (`config_version`). All rules below are configuration, not judgment.

## Stage order (default)

`outreach → nda → access → diligence → bid → approval`

A party's `stage` is where it sits in this sequence; `stage_order` may be overridden per
deployment. Stage position drives the control gates below and the stage roll-up counts.

## Status vocabularies

| Field | Typical values |
| ----- | -------------- |
| `engagement` | `active`, `declined`, `withdrawn` (non-active parties are tracked but **not** gated) |
| `nda_status` | `none`, `sent`, `executed` |
| `access_status` | `none`, `requested`, `granted` |
| milestone `status` | open states vs. **done** states: `complete`, `completed`, `done`, `received`, `executed`, `satisfied`, `closed` |

Milestones in a **done** state are excluded from reminders. Bids carry `type` (`IOI`/`LOI`/
`binding`), `amount`, `currency`, `received_date`, and a `source_ref`.

## Deterministic control gates (surfaced as control-exception open items)

For **active** parties only:

| Gate | Condition | Exception |
| ---- | --------- | --------- |
| NDA before access | access `granted`, or stage ≥ `access`, while `nda_status` ≠ `executed` | `nda-not-executed` |
| Access before diligence | stage ≥ `diligence` while `access_status` ≠ `granted` | `access-not-granted` |

A breach is **flagged and escalated**; the party is never advanced or auto-corrected. Output
validation fails closed if a matching breach is not flagged.

## Reminder logic (deterministic)

- Computed against `as_of_date` with a reminder lookahead window (`reminder_lookahead_days`,
  default **7**).
- A milestone with a valid `due_date` and an open status is **overdue** if `due_date <
  as_of_date`, otherwise **due-soon** if `due_date ≤ as_of_date + lookahead`.
- Overdue milestones also become **open items**. Undated open milestones cannot be reminded
  (a `validate_input` warning), so they are surfaced as data gaps rather than guessed.

## Change log (auditable)

Diff of the current state vs. the **prior snapshot** on the tracked fields `stage`,
`nda_status`, `access_status`; a party absent from the prior snapshot is logged as `added`.
Each entry records `from`, `to`, and the `as_of` date for reproducibility.

## Approvals

`required_approvals` (e.g. `deal-committee-approval`, `conflicts-clearance`) are captured
from the governance system. Recorded approvals carry type + role + approver + date +
citation; any required approval not recorded appears as **outstanding** and as an open item
("obtain the required approval before any external delivery").

## Hard boundaries (fail closed)

- No **bid selection**, **counterparty recommendation**, or **exclusivity award**.
- No **execution**: never send outreach, execute/sign an NDA, grant data-room access, submit
  a bid, or deliver the tracker.
- No **fabricated or advanced status**; every hard fact is cited or it is a data gap.
- No **investment advice**; the tracker organizes process facts only.

## Tracker (output) — required contents

Durable `process_id`; `as_of_date`; `config_version`; per-party stage / NDA / access / bid
with citations and any control exceptions; overdue and due-soon reminders; auditable change
log; recorded and outstanding approvals; open-items list; source index; `tracker_status`
`draft-tracker`; and the standing note.
