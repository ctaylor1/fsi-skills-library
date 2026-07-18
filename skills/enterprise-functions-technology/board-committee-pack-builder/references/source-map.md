# Source Map — board-committee-pack-builder

The pack is only as trustworthy as its citations. Every substantive line in the pack maps
to one entry in the approved-source register; a claim without a resolvable source is an
**unsupported assertion** and blocks the draft.

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Controlled content library** (approved templates, minutes, prior packs) | Template version, minutes, matters arising | Read-only |
| 2 | **Management reporting / finance** | KPI/metrics values, financial results | Read-only |
| 3 | **Risk register / ERM + KRI monitor** | Risks, ratings, indicator breaches | Read-only |
| 4 | **Project / action tracking** | Open issues, actions, owners, due dates | Read-only |
| 5 | **Documents, contracts, procurement, knowledge systems** | Supporting evidence for specific agenda items | Read-only |
| 6 | **Email / calendar** | Meeting date, attendees, logistics (non-substantive) | Read-only |

## Citation format

`{system}:{ref}@{as_of}` — e.g. `management-reporting:MRP-2026-07@2026-07-15`,
`risk-register:ERM-2026-Q3@2026-07-10`, `minutes:AC-2026-05-minutes@2026-05-06`.

## Freshness / effective dates

- Every source carries an `as_of` date; the pack shows it so readers see how current each
  figure is. Stale sources are cited **with their date**, never silently refreshed.
- The `template_version` is a **versioned contract**: the pack is assembled against the
  approved template revision and records which revision was used.
- Conflicting figures between two sources are surfaced side by side with both citations and
  routed to the content owner; the skill does not pick a winner.

## Least-privilege operations (deployment)

- `content.get(template, version)`, `minutes.read(committee, period)` — read-only.
- `reporting.read(metric, period)`, `risk.read(register|kri, as_of)`,
  `actions.read(committee, open)` — read-only, bounded.
- `docs.read(ref)` for supporting evidence — read-only.
No mutation from this skill. It never posts to a board portal, emails the pack, or writes to
any system of record; external delivery is a separate, human-performed step.
