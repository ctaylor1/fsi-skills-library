<!--
Output template — transaction-process-tracker (Draft & package)
Human-facing render of the tracker manifest produced by scripts/calculate_or_transform.py.
The section headers below mirror the canonical manifest `sections` keys, which
scripts/validate_output.py enforces as a versioned contract:
  Process Summary -> process_summary   Party Tracker -> party_tracker
  Approvals       -> approvals          Reminders     -> reminders
  Change Log      -> change_log          Open Items    -> open_items
  Source Index    -> source_index
Fill every {{placeholder}} from cited sources only. Do not add a bid recommendation,
counterparty selection, or any send/grant/deliver statement. This is a DRAFT for human review.
-->

# Transaction Process Tracker (DRAFT) — {{deal_name}}

**Process ID:** {{process_id}} | **As of:** {{as_of_date}} | **Config:** {{config_version}}
**Status:** draft-tracker — internal deal-team review only; not delivered.

## Process Summary
- Parties: {{parties_total}} ({{by_engagement}}) | Stages: {{by_stage}}
- Reminders: {{reminders_overdue}} overdue, {{reminders_due_soon}} due-soon
- Control exceptions: {{control_exceptions}} | Open items: {{open_items_total}}
- Approvals: {{approvals_recorded}} recorded, {{approvals_outstanding}} outstanding

## Party Tracker
| Party | Type | Engagement | Stage | NDA | Access | Bid | Exceptions | Source |
| ----- | ---- | ---------- | ----- | --- | ------ | --- | ---------- | ------ |
| {{name}} | {{type}} | {{engagement}} | {{stage}} | {{nda_status}} | {{access_status}} | {{bid}} | {{exceptions}} | {{citation}} |
<!-- one row per party; every row MUST carry a source citation; bids MUST be cited -->

## Approvals
- **Recorded:** {{type}} — {{approver_role}} — {{date}} ({{citation}})
- **Outstanding:** {{type}} — {{status}}
<!-- required approvals not yet recorded appear here and as open items -->

## Reminders
- **Overdue:** {{party}} — {{milestone label}} — due {{due_date}} ({{citation}})
- **Due soon:** {{party}} — {{milestone label}} — due {{due_date}} ({{citation}})

## Change Log
| Party | Field | From | To | As of |
| ----- | ----- | ---- | -- | ----- |
| {{party_id}} | {{field}} | {{from}} | {{to}} | {{as_of}} |
<!-- diff vs. the prior snapshot on stage / nda_status / access_status; additions noted -->

## Open Items
- {{item}} — {{type}} — {{action}} ({{citation}})
<!-- control exceptions and overdue milestones are escalated, never auto-resolved -->

## Source Index
- {{system}}:{{ref}}@{{date}}
<!-- de-duplicated list of every citation used above -->

---
**Standing note:** Draft transaction process tracker for internal deal-team review only. It
records status, reminders, and a change log; it is not a deal decision, bid selection, or
recommendation, and no outreach, NDA, data-room access, or delivery has been executed.
External delivery or any system-of-record change requires the named human owner's approval.
