# Source Map — relationship-manager-client-briefer

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Commercial CRM** | Client/party identity (system of record for the relationship), contacts, pipeline/opportunities, relationship-review notes, open actions | Read-only |
| 2 | **Core banking / loan servicing** | Facility exposures (committed / outstanding), product holdings | Read-only |
| 3 | **Covenant tracking** | Covenant definitions, latest test results and status | Read-only |
| 4 | **Profitability / RAROC** | Revenue-to-bank, profitability and return metrics | Read-only |
| 5 | **Service / case management** | Open service cases and issues | Read-only |
| 6 | **News / media** | Recent news and adverse-media flags (surfaced only; not adjudicated) | Read-only |
| 7 | **Controlled template & content library** | Approved brief template, section order, standing disclaimer | Read-only |

The commercial CRM is authoritative for who the client is and who the contacts are; core
banking is authoritative for exposures and products; covenant tracking for covenant status;
profitability for return metrics. The approved brief template is a **versioned contract** —
record the template version and `as_of_date` on every brief. Never state a fact, figure,
exposure, covenant status, or news item that a listed source does not support.

## Citation format

`{system}:{ref}@{date}` — e.g. `crm:party=CRM-88101@2026-07-15`,
`core-banking:exposures=EXP-4410@2026-07-14`, `covenants:test=COV-2201@2026-07-13`,
`profitability:raroc=PRF-771@2026-07-12`, `news:item=NWS-5501@2026-07-16`.

## Freshness / effective dates

- Every content item carries the `date` of its source. Two thresholds apply relative to
  `as_of_date`:
  - **Critical** sources (exposures, covenants, profitability) use `critical_freshness_days`
    (default **10**). Credit and covenant context goes stale fast; a stale critical source
    misrepresents the client's current risk position.
  - All other sources use `freshness_days` (default **30**).
- A cited source older than its threshold and not explicitly acknowledged (`stale_ack: true`)
  flags the client `stale-source` — the brief is **not** packaged until the source is
  refreshed or the staleness is acknowledged (e.g., an intentionally historical figure).
- The brief always records the `as_of_date` it was assembled against.

## Least-privilege operations (deployment)

- `crm.get_party(client_id)` / `crm.list_contacts|opportunities|actions(client_id)` — read-only.
- `core_banking.get_exposures(client_id)` / `core_banking.list_products(client_id)` — read-only, bounded.
- `covenants.get_status(client_id)` — read-only.
- `profitability.get_metrics(client_id, period)` — read-only.
- `service.list_cases(client_id)` / `news.search(entity)` — read-only.
- `templates.get('rm-client-brief', version)` — read-only controlled content.

No mutation from this skill. Sending, submitting, or delivering the brief and any CRM /
system-of-record write are **out of scope** — performed by an authorized human after review.
