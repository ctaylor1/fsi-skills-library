# Source Map — advisor-follow-up-assistant

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **CRM / meeting record** | Meeting date, attendees, discussion points, action items, next-review target (system of record for the client relationship) | Read-only |
| 2 | **Planning engine** | Objectives, goals, distribution timing that the summary and action items reference | Read-only |
| 3 | **Portfolio accounting / OMS** | Current holdings, allocation drift, liquidity balances referenced in the summary | Read-only |
| 4 | **Product data** | Instrument / benchmark facts referenced in any recommendation discussed | Read-only |
| 5 | **Disclosures / restrictions register** (versioned) | Required disclosures for a recommendation; client restrictions | Read-only |
| 6 | **Approved tax-assumptions set** (versioned) | Any tax figure referenced in the summary or communication | Read-only |
| 7 | **Controlled follow-up template + disclosures library** (versioned) | Required sections, layout, approved disclosure language | Read-only |

## Citation format

`{system}:{ref}@{date/version}` — e.g. `crm:meeting=HH-4821-20260714@2026-07-14`,
`planning:objectives=HH-4821@2026-07-10`, `oms:alloc=****7731@2026-07-12`,
`disclosures:std@v2026.07`, `template:followup-standard@v2026.07`.

Every **material assertion** (see [domain-rules.md](domain-rules.md)) — meeting summary, each action
item, the client communication, each disclosure, each CRM field, and the next-meeting reminder —
must carry a citation. An uncited material assertion is unsupported and fails the output screen.

## Freshness / effective dates

- The meeting record, holdings, and allocation drift must be read fresh; the draft reflects the
  meeting as documented, not a later state.
- The **follow-up template** and the **disclosures library** are versioned; the versions in use are
  recorded on the draft for reproducibility and review. A stale template/disclosures version stops
  the build (fail closed).

## Least-privilege operations (deployment)

- `crm.meeting.read(household_id, meeting_id)`, `crm.profile.read(household_id)` — read-only.
- `planning.objectives.read(household_id)` — read-only.
- `oms.holdings.read(account_id)`, `oms.alloc.read(account_id)` — read-only, bounded.
- `product.reference.read(instrument|benchmark)` — read-only.
- `register.disclosures.get(version)`, `template.followup.get(version)` — read-only, versioned.

No mutation from this skill. The follow-up package is produced for advisor review; **no** send,
CRM write, scheduling, delivery, or trade is initiated. Any send, CRM update, or approval happens
out-of-band through the permission/approval broker, recorded against the `followup_id` as a human
action — never by this skill.
