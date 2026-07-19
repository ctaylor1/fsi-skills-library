# Source Map — portfolio-proposal-comparator

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Portfolio-accounting / OMS** (position of record) | Each proposal's holdings and weights | Read-only |
| 2 | **Product data** | Expense ratio, share class, liquidity, surrender terms, proprietary/revenue-sharing status | Read-only |
| 3 | **Planning engine** | Stated objectives, constraints, benchmarks the proposals are measured against | Read-only |
| 4 | **CRM** | Client identity, stated objective/risk tolerance, prior context | Read-only |
| 5 | **Disclosures / restrictions** | Product availability, restricted lists, required disclosures | Read-only |
| 6 | **Approved config** (versioned) | Concentration/liquidity/cost thresholds, approved tax assumptions | Read-only |

Never substitute a marketing sheet or a client assertion for the OMS/product record. If the OMS and a
product sheet conflict (e.g., different expense ratio or share class), cite both and flag for the
reviewer — do not resolve silently.

## Citation format

`proposal:{proposal_id};{source_ref}` — e.g. `proposal:P-B;holdingid=H-B1`. Every flag and every
material difference cites the specific holding/proposal rows and the threshold applied.

## Freshness / effective dates

- Config (thresholds, tax assumptions) is a **versioned contract**; the output records the
  `config_version` used so a comparison is reproducible.
- Proposal holdings are as-of the OMS snapshot date; state the `as_of` in the output.
- Product attributes (expense ratio, share class, liquidity) must be current as of the same as-of; a
  stale product record silently changes cost and liquidity flags.

## Least-privilege operations (deployment)

- `oms.holdings(proposal_id)` → bounded holding rows for a proposal.
- `product.attributes(security_id)` → expense ratio, share class, liquidity, proprietary/revenue-share.
- `planning.objectives(client_id)` → stated objective, constraints, benchmark.
- `crm.context(client_id)` → identity, stated objective/risk tolerance.
- `config.get('proposal-comparator', version)` → thresholds + approved tax assumptions.

All read-only, deterministic, durable `comparison_id`, below the fixed timeout; page long proposals as
resumable stages. No write, submission, trade, or system-of-record operation is exposed by this skill.
