# Source Map — merchant-fee-optimizer

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Processor/acquirer statement + settlement** (position of record) | Volume, fees charged, interchange/assessment/markup lines, downgrades | Read-only |
| 2 | **Gateway / processor transaction detail** | Per-transaction card type, entry mode, Level 1/2/3 data, interchange category | Read-only |
| 3 | **Card-network rules & interchange schedules** (versioned) | Interchange categories, qualification criteria, assessment rates | Read-only |
| 4 | **Merchant contract / pricing terms** | Pricing model, markup, monthly fees, term, auto-renew, early-termination fee | Read-only |
| 5 | **Fee-optimization benchmarks config** (versioned) | Markup benchmark, Level 2/3 savings bps, recoverable share, savings bands | Read-only |

The **processor statement/settlement is the position of record** for what was actually
charged. Interchange schedules and network rules are the authority for *category
qualification*; never assert a downgrade or a Level 2/3 saving without tying it to the
current published schedule. If the statement and the network schedule conflict, cite both
and flag for the reviewer — do not silently "correct" the statement.

## Citation format

`stmt:{source_ref}@{period}` — e.g. `stmt:mid=****4321;txnid=T-07@2026-06`, and
`stmt:mid=****4321;line=processor_markup@2026-06` for statement-level lines. Every fired
opportunity cites the specific transactions or statement lines behind it and the estimate's
basis.

## Freshness / effective dates

- Interchange rates and network assessments **change (typically twice a year and via network
  releases)**. The analysis records the `config_version` and the statement `period` so a run
  is reproducible; estimates must be validated against the schedule in effect for the period.
- Benchmarks (markup benchmark, Level 2/3 bps, recoverable share, savings bands) are a
  **versioned contract** owned by the payments-operations team, never guessed per merchant.
- Analyze a stated statement period; do not blend periods without labeling them.

## Least-privilege operations (deployment)

- `statement.get(merchant_id, period)` → fee summary + line items (masked MID).
- `txns.read(merchant_id, period)` → bounded, paged transaction detail with card type, entry
  mode, level, interchange category.
- `networkrules.get(scheme, effective_date)` → interchange categories + qualification +
  assessment rates (read-only, versioned).
- `contract.get(merchant_id)` → pricing model, markup, monthly fees, term, ETF.
- `config.get('merchant-fee', version)` → benchmarks + savings bands.

All read-only, deterministic, durable `analysis_id`, below the fixed timeout; page long
transaction histories as resumable stages. No write to any processor, contract, or ledger
system of record.
