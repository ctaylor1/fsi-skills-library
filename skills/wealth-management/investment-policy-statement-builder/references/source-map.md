# Source Map — investment-policy-statement-builder

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **CRM / planning engine** | Client profile, objectives, risk tolerance, time horizon, governance (system of record for the profile) | Read-only |
| 2 | **Portfolio accounting / OMS** | Holdings, account structure, current allocation, liquidity balances | Read-only |
| 3 | **Product data** | Permitted instruments, benchmarks, product features | Read-only |
| 4 | **Disclosures / restrictions register** | Legal/regulatory constraints, client restrictions, required disclosures | Read-only |
| 5 | **Approved tax-assumptions set** (versioned) | Marginal rate, account-type treatment, approved tax figures | Read-only |
| 6 | **Controlled IPS template library** (versioned) | Required sections, layout, standard disclosure language | Read-only |

## Citation format

`{system}:{ref}@{date/version}` — e.g. `crm:profile=HH-4821@2026-07-10`,
`oms:acct=****7731;alloc@2026-07-12`, `tax:approved-set@v2026.2`,
`register:restriction=RST-014@2026-06-30`, `template:ips-standard@v2026.07`.

Every **material assertion** (see [domain-rules.md](domain-rules.md)) and every strategic-allocation
line must carry a citation. An uncited material figure is an unsupported assertion and fails the
output screen.

## Freshness / effective dates

- Client profile, objectives, and risk tolerance must be read fresh from CRM/planning; a refresh
  supersedes a prior IPS and records what changed.
- The **IPS template** and the **approved tax-assumptions set** are versioned; the versions in use
  are recorded on the draft for reproducibility and review. A stale template/tax version stops the
  build (fail closed).

## Least-privilege operations (deployment)

- `crm.profile.read(household_id)`, `planning.objectives.read(household_id)` — read-only.
- `oms.holdings.read(account_id)`, `oms.liquidity.read(account_id)` — read-only, bounded.
- `product.reference.read(instrument|benchmark)` — read-only.
- `register.restrictions.read(household_id)` — read-only.
- `tax.assumptions.get(version)`, `template.ips.get(version)` — read-only, versioned.

No mutation from this skill. The draft IPS is produced for human review; **no** delivery, signature,
system-of-record write, or trade is initiated. Any approval or delivery happens out-of-band through
the permission/approval broker, recorded against the `ips_id` as a human action — never by this skill.
