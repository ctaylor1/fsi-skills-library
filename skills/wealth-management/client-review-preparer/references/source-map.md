# Source Map — client-review-preparer

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Wealth CRM** | Household/client identity, advisor of record, contacts, prior meeting notes, service history, life events, open actions | Read-only |
| 2 | **Portfolio accounting / custody** | Accounts, registrations, reported account values, holdings, market values (system of record for positions) | Read-only |
| 3 | **Performance** | Time-weighted returns, benchmarks, periods | Read-only |
| 4 | **Planning engine** | Goals, targets, plan items, funding assumptions | Read-only |
| 5 | **Product & disclosure library** | Required disclosures (Form CRS, Reg BI, fee schedule, performance disclosure), product facts | Read-only |
| 6 | **Disclosure / review config** (versioned) | Required-disclosure set per review type, freshness thresholds | Read-only |

## Citation format

`{system}:{ref}@{date}` — e.g. `custody:stmt=****3300@2026-07-15`,
`portfolio:holdings=****3300@2026-07-14`, `planning:plan=PL-771@2026-07-01`,
`disclosure-library:pack=DISC-2026@2026-07-10`. Every item in the pack cites a source in
the review's inventory; nothing enters the pack without a citation.

## Freshness / effective dates

- `as_of_date` drives freshness and overdue-action calculations.
- **Holdings and performance** are *critical* content: their cited sources go stale under the
  tighter `critical_freshness_days` (default 7). A stale critical source blocks assembly
  unless explicitly acknowledged (`stale_ack: true`).
- All other content uses `freshness_days` (default 30).
- The required-disclosure set and freshness thresholds are a **versioned config contract**;
  the `config_version` is recorded on the output for reproducibility.

## Least-privilege operations (deployment)

- `crm.read(client_id)` → identity, advisor, notes, service history, life events, actions.
- `portfolio.read(account_id)` / `custody.read(account_id)` → accounts, reported values, holdings.
- `performance.read(scope, period)` → returns/benchmarks.
- `planning.read(plan_id)` → goals, plan items.
- `disclosures.read(review_type)` → required disclosure set + documents.
- `config.get('wm-review', version)` → required disclosures + freshness thresholds.

No mutation from this skill. It never writes the CRM/book of record, never delivers the pack,
and never stages a trade. Delivery, CRM writes, and any recommendation/trade are separate
human-authorized actions outside this skill.
