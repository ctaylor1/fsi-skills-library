# Source Map — order-allocation-validator

## Source hierarchy (highest first)
| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | OMS/EMS **allocation record** (system of record) | Order, fills, proposed per-account lines, timestamps | Read-only |
| 2 | Client/account **eligibility & entitlements** | Account eligibility, restrictions | Read-only |
| 3 | Approved **allocation-policy config** (versioned) | Method, tolerance, deviation-approval rule | Read-only |
| 4 | Reference data | Security/lot-size normalization | Read-only |

Never let a proposed line override the executed-fill record; if they conflict, cite both and
route the break.

## Citation format
`{system}:{ref}@{ts/version}` — e.g. `oms:order=ORD-8841;alloc-line=****3300@2026-07-18T15:41`,
`policy:allocation@v2026.05`. Every exception cites its evidence line and the policy rule/version.

## Freshness / effective dates
- Policy config is a **versioned contract**; the output records the version used.
- Use the executed-fill quantity/price as of the order; flag mixed as-of.

## Least-privilege operations (deployment)
- `oms.read_allocation(order_id)` → order + proposed lines — read-only, bounded.
- `entitlements.read(account_id)` → eligibility flags — read-only.
- `config.get('allocation', version)` → method/tolerance/rules — read-only.
Durable `validation_id`; below the fixed timeout; no mutation.
