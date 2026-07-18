# Source Map — post-trade-settlement-monitor

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Post-trade / clearing** (CSD, custodian, CCP status) — position of record | Settlement status, matched/affirmed/failed state, penalties | Read-only |
| 2 | **OMS/EMS** | Trade economics, intended settlement date (ISD), direction, quantity, cash | Read-only |
| 3 | **Market & reference data** | Security/ISIN resolution, market cutoff times, buy-in windows, market calendar | Read-only |
| 4 | Settlement-ops **config** (versioned) | Alert thresholds, aging bands, materiality, staleness window, severity map | Read-only |
| 5 | **Regulatory reporting / surveillance / communications archive** | Cross-checks (e.g., CSDR penalty feeds, SFTR/transaction-reporting linkage) | Read-only |

The clearing/CSD status is the **position of record** for whether an instruction has
settled. If OMS/EMS and clearing disagree (e.g., OMS shows settled, CSD shows failed), cite
both and raise the discrepancy — never silently prefer the more convenient source.

## Citation format

`clearing:{source_ref}@{source_as_of}` — e.g.
`clearing:acct=****BRK;instr=INS-BRK01@2026-07-17T15:09:00`. Every alert cites the specific
instruction row and the feed timestamp it was read from.

## Freshness / effective dates

- Each instruction carries `source_as_of`; the run carries `as_of`. If
  `as_of − source_as_of > max_source_staleness_minutes` the row is **stale**: the monitor
  still surfaces it but flags it in `freshness.stale_instruction_ids` and requires a re-pull
  before reliance. Staleness is never used to silently suppress an alert.
- Cutoff times and the market calendar are **effective-dated** reference data; business-day
  aging must use the deployment market calendar (this repo's stdlib fallback counts Mon–Fri).
- Config (thresholds, bands, severity map) is a **versioned contract**; the output records
  `config_version` so a run is reproducible.

## Least-privilege operations (deployment)

- `clearing.status(book|as_of)` → bounded, paged instruction rows with settlement state.
- `oms.economics(trade_ids)` → ISD, direction, quantity, cash, currency.
- `refdata.resolve(security|market)` and `refdata.cutoffs(market, date)` → normalized values.
- `config.get('settlement', version)` → thresholds + severity map.
- `queue.open_alerts(book)` → currently-open alert dedup keys (read, for deduplication).

All read-only, deterministic, durable `run_id`, below the fixed timeout; page long books as
resumable stages. The monitor holds **no write, cancel, match, or settle entitlement**.
