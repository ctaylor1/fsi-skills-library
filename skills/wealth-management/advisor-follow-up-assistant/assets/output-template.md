# Advisor Follow-Up Package (DRAFT) — {{followup_id}}

> Draft status: **{{draft_status}}** · Delivery status: **{{delivery_status}}** · CRM write: **{{crm_write_status}}**
> Template version: `{{template_version}}` · Disclosures version: `{{disclosures_version}}`
> Prepared: {{prepared_date}} by {{author_id}} · Meeting: {{meeting_date}}
>
> **Standing note:** Draft follow-up package for human review only; nothing has been sent to the
> client, no CRM or system of record has been updated, no trade has been placed, and no
> suitability determination has been made.

Complete all 7 sections. Every material assertion carries a citation in the form
`{system}:{ref}@{date/version}`. Do not remove, reorder, or rename sections — the output
validator checks each required section by title.

---

## 1. Meeting Summary
What was discussed, who attended, the channel, and the key points raised — as documented in the
meeting record, not inferred. Client and account identifiers masked to what the summary requires.
_Citations:_ {{meeting_summary_citations}}

## 2. Action Items
Each item has an owner, a due date, and a source. Items assigned to the client are requests for
the client to consider, not commitments made on their behalf.

| ID | Owner | Description | Due | Citation |
| -- | ----- | ----------- | --- | -------- |
| {{action_id}} | {{action_owner}} | {{action_desc}} | {{action_due}} | {{action_citation}} |

## 3. Client Communication (Draft)
Draft email / letter / portal message for advisor review before any send. Written as a summary and
proposed next steps, phrased for confirmation — no commitments, no guarantees, no performance
promises, and no statement that any action has already been taken.
_Channel:_ {{comm_channel}} · _Subject:_ {{comm_subject}}
_Citations:_ {{communication_citations}}

## 4. Disclosures
Required disclosures drawn from the controlled disclosures library (versioned above). Every
recommendation discussed that requires a disclosure is covered here by its recommendation ID. If no
new recommendation was discussed, this section records that no product-specific disclosure is
required, citing the meeting record.
_Citations:_ {{disclosures_citations}}

## 5. CRM Update (Proposed)
Field-level changes **proposed** for the advisor to review and apply — this skill does not write to
the CRM or any system of record.

| Field | Proposed value | Citation |
| ----- | -------------- | -------- |
| {{crm_field}} | {{crm_value}} | {{crm_citation}} |

## 6. Next-Meeting Reminder
Proposed timeframe and purpose for the next review, for the advisor to confirm and schedule. Not a
calendar invite and not sent.
_Citations:_ {{next_meeting_citations}}

## 7. Approvals and Delivery
Recorded as **pending** — completed by humans out-of-band. The package is not sent, the CRM is not
updated, and nothing is scheduled until the advisor (and, where required, a supervisory principal
per FINRA Rule 2210) approves.

| Role | Name (masked) | Status | Date |
| ---- | ------------- | ------ | ---- |
| Advisor | {{advisor}} | pending | — |
| Supervisory Principal | {{principal}} | pending | — |

_Delivery status:_ **not-delivered** · _CRM write status:_ **not-written**

---

### Routing (handoffs recorded, not executed)
{{routes}}

### Source map
{{section_key}} → {{citations}} …

### Data gaps (needs-data)
{{gaps}}
