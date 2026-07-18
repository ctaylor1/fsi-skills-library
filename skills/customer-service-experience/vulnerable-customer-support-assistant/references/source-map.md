# Source Map — vulnerable-customer-support-assistant

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Contact-center transcript / chat** | The customer's own words — the only basis for a support signal | Read-only |
| 2 | **CRM** (system of record) | Customer profile, existing (human-set) support markers, prior notes | Read-only |
| 3 | **Case management** | Case/interaction context, channel, `assessment_id` linkage | Read-only |
| 4 | **Complaint system** | Complaint text when the interaction is complaint-driven | Read-only |
| 5 | **Approved knowledge / product terms** | What an accommodation means and whether it applies to the product | Read-only |
| 6 | Approved **drivers taxonomy + accommodations catalog + referral routes** (versioned) | Signal mapping, accommodation selection, referral | Read-only |

## Citation format

`{system}:{ref}@{when}` — e.g. `transcript:call=CC-8842;line=41@2026-07-16`,
`crm:cust=****4417@2026-07-16`, `config:vuln-support@v2026.06`. Every observed signal cites the
transcript/chat line it was said on; every accommodation and referral cites the signal(s) that
support it.

## Freshness / effective dates

- Read the interaction fresh; a support need may be tied to a **current** life event and may be
  transient. Do not carry an old signal forward as a standing fact.
- The drivers taxonomy, accommodations catalog, and referral routes are **versioned**; the
  version is recorded on every assessment for reproducibility and review.

## Least-privilege operations (deployment)

- `transcript.read(interaction_id)`, `chat.read(interaction_id)` — read-only.
- `crm.read(customer_id)` — read-only; the skill **never** writes a marker or accommodation.
- `case.read(case_id)`, `complaint.read(complaint_id)` — read-only.
- `config.get('vuln-support', version)` — read-only.
No mutation from this skill. Recording a support marker, applying an accommodation, and making a
referral are **proposals** carried out by an authorized human via the approval broker.
