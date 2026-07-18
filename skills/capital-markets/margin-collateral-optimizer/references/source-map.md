# Source Map — margin-collateral-optimizer

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Clearing / CSA eligibility & haircut schedules** (CCP rulebook, ISDA CSA / Credit Support Annex) | What is eligible per agreement, and the haircut per asset class | Read-only |
| 2 | **Collateral inventory** (position of record: custody / collateral-management system) | Available assets, market value, currency, encumbrance | Read-only |
| 3 | **Margin calls** (post-trade / clearing, counterparty statements) | Call amount, type (VM/IM), agreement, currency, due time | Read-only |
| 4 | **Market & reference data** | Security valuation, asset-class taxonomy, liquidity classification (HQLA level) | Read-only |
| 5 | **Funding / pledge-cost curve** (treasury) | `pledge_cost_bps` per asset — the opportunity cost of posting it | Read-only |
| 6 | **Concentration-limit config** (versioned) | Per-call / per-class concentration caps | Read-only |

The **eligibility & haircut schedule is the authority** on what may be delivered and at what
haircut — never substitute a trader's or counterparty's assertion for the agreement terms.
If the collateral inventory and a counterparty statement disagree on availability, cite both
and flag for the reviewer; do not resolve silently.

## Citation format

Each allocation line cites both the inventory row and the applicable haircut-schedule entry:
`inv:{inventory_ref}|hc:{schedule_ref}` — e.g.
`inv:inv;asset=A-UST1@2026-07-15|hc:clearing-rulebook;CCP-ALPHA;ust@2026-07-01`. The call
itself carries its own `source_ref`.

## Freshness / effective dates

- Eligibility, haircuts, and concentration limits are **versioned contracts**; the output
  records `config_version` so a recommendation is reproducible.
- Valuations and calls are **as-of** a stated timestamp; state the exact `as_of` in the
  output. A recommendation computed on stale marks or a superseded schedule is invalid.
- Haircut-schedule effective dates must be on/before `as_of`; a future-dated schedule is not
  yet in force.

## Least-privilege operations (deployment)

- `eligibility.get(agreement_id)` → eligible classes + haircuts (versioned).
- `inventory.read(portfolio_id, as_of)` → available assets, market value, encumbrance.
- `calls.read(portfolio_id, as_of)` → open margin calls (amount, type, agreement, currency).
- `refdata.value(security)` / `refdata.classify(asset_class)` → marks and taxonomy.
- `funding.curve(as_of)` → pledge-cost basis points per asset/class.
- `limits.get('collateral', version)` → concentration caps.

All read-only, deterministic, durable `recommendation_id`, below the fixed timeout; page long
inventories as resumable stages. No operation pledges, moves, substitutes, or settles
collateral, and none disputes or accepts a margin call — those are human/authorized-system
actions in the collateral-management and settlement systems.
