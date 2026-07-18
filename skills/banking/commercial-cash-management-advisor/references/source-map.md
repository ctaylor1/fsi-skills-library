# Source Map — commercial-cash-management-advisor

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | Core-banking **balances & activity analytics** (position of record) | Account balances, operating-activity volumes | Read-only |
| 2 | **CRM** relationship context | Existing services, entity structure, relationship notes | Read-only |
| 3 | **Product terms** (controlled content library) | What each treasury service requires and excludes | Read-only |
| 4 | **Loan origination/servicing** | Existing facilities/overdraft protection when a liquidity referral is raised | Read-only |
| 5 | TM **product/config** (versioned) | Service-fit thresholds and priority mapping | Read-only |

Never substitute a client assertion for the balance/activity record. If the record and a CRM
note conflict, cite both and flag for the reviewer. Pricing and rate tables are **not** an
input here — this skill does not price.

## Citation format

`{system}:{ref}` — e.g. `cb:acct=****1001;stmt=2026-06` for a balance row or
`cb:acct=****1001;analytics=2026Q2` for an activity metric. Every recommended service cites
the specific evidence rows and the basis/threshold used.

## Freshness / effective dates

- Config (thresholds, mapping) is a **versioned contract**; the output records the config
  version used so an advisory is reproducible.
- Balances and volumes are **period averages**; the output states the analysis period. State
  seasonality caveats where a single period may not represent the year.
- Existing-services list from CRM must be current so the skill does not re-recommend a service
  the client already has.

## Least-privilege operations (deployment)

- `cb.balances(customer_id, period)` → account group with average collected/ledger balances.
- `cb.activity(customer_id, period)` → aggregated operating-activity volumes.
- `crm.relationship(customer_id)` → existing services, entity structure, notes.
- `product.terms(service)` → eligibility/requirements for a candidate service (no pricing).
- `config.get('tm-fit', version)` → thresholds + priority mapping.

All read-only, deterministic, durable `advisory_id`, below the fixed timeout; page long
account groups as resumable stages. No pricing, credit, investment, or enrollment operation
is bound by this skill.
