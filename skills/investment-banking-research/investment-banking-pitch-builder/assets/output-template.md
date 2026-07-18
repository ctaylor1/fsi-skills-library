# Pitch-Book Draft - Output Template

> DRAFT - for internal banker and compliance review only. Not for external distribution
> until the required approvals are recorded. This skill never sends, delivers, distributes,
> or files materials.

Fill every field from **approved sources**. Do not originate figures here; cite the upstream
component. Any page missing a takeaway, a source, an approved claim, or content approval is
**blocked** (not `ready`). Required template sections must all be present.

---

## Header

- **Engagement:** `{engagement_id}`
- **Client / project:** `{deal_context.client_name}`
- **Mandate:** `{deal_context.mandate_type}`  ·  **Audience:** `{deal_context.audience}`
- **Template:** `{template_id}@{template_version}`
- **Data classification:** Highly Confidential (MNPI / client-confidential)
- **Delivery status:** `{draft | hold-for-approval | approved-for-delivery}`  *(never a delivered state)*

## Required sections (template fidelity)

Present: `{sections_present}`  ·  Missing: `{sections_missing}` *(must be empty to deliver)*

Default required sections: `cover`, `executive-summary`, `market-overview`, `valuation`,
`process-and-timeline`, `disclaimer`.

## Pages

For each page, in template-section order:

| Field | Content |
| ----- | ------- |
| Page ID | `{page_id}` |
| Section | `{section}` |
| Title | `{title}` |
| Source component | `{source_component}` (upstream skill or `manual`) |
| Takeaway ("so what") | `{takeaway}` |
| Claims | each: `{text}` -> `source_ref` `{ref@date}` (approved: yes) |
| Sources | `{[system:ref@date, ...]}` |
| Content approval | `{approver}` on `{date}` (status: approved) |
| Status | `ready` \| `needs-source` \| `unsupported-claim` \| `needs-approval` |

## Unsupported / blocked items

List every page whose status is not `ready` and every claim lacking an approved
`source_ref`. These must be resolved (route to the upstream skill) before delivery -
**never** back-filled with an estimated figure.

## Required approvals (recorded before external delivery)

| Role | Owner | Status | Approver | Date |
| ---- | ----- | ------ | -------- | ---- |
| `banker_signoff` | Deal-captain / MD | approved / pending | | |
| `compliance_control_room` | Control room / compliance | approved / pending | | |
| `legal_disclaimers` | Legal | approved / pending | | |

`approved-for-delivery` requires **all** rows `approved`.

## Standing note (required)

> Draft pitch materials only; no materials have been sent, delivered, distributed, or
> filed. External delivery requires the recorded banker, control-room/compliance, and
> legal/disclaimer approvals and is performed by a person, not this skill.
