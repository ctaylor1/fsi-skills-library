# Source Map — position-cash-reconciliation-assistant

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Accounting / IBOR (books of record)** (internal position of record) | The fund's internal positions and cash being reconciled | Read-only |
| 2 | **Custodian** (independent confirmation) | Custody-confirmed holdings and cash balances per account | Read-only |
| 3 | **Prime broker** (independent confirmation) | Financed positions, margin, and cash at the PB | Read-only |
| 4 | **Fund administrator** (independent confirmation) | Administrator holdings, cash, accruals, and shadow records | Read-only |
| 5 | **Counterparty** (independent confirmation) | OTC/derivative positions and collateral cash confirmed by the counterparty | Read-only |
| 6 | Reconciliation **config** (versioned) | Tolerances, materiality, pending-settlement window, fx rates | Read-only |
| 7 | Prior-period **reconciliation** (durable `reconciliation_id`) | Carry-forward of open reconciling items | Read-only |

The internal book and each external source are **two independent positions of record**; neither is
subordinate to the other. The external record is the independent confirmation, so a proposed item is
framed as bringing the internal book to agree to it — but a break is a disagreement between them, and
the skill classifies and evidences it, it does **not** decide which side is "right" or overwrite
either. If a source assertion conflicts with the recorded position/cash, cite both and flag for the
reviewer.

## Input schema (validated by `scripts/validate_input.py`)

Top level: `entity`, `as_of` (YYYY-MM-DD), `config_version`, `base_currency`, `internal_records[]`,
`external_records[]`, `config{}`.

Each record (`internal_records[]` / `external_records[]`):
`record_id` (unique across the job), `match_key`, `account`, `source_system`
(external ∈ {`custodian`, `prime_broker`, `administrator`, `counterparty`}), `record_type`
(`position` | `cash`), `quantity` (positions) **or** `amount` + `currency` (cash), `date`,
`settle_date` (defaults to `date`), `source_ref`, `description`, optional `route_hint`
(`trade_discrepancy`).

`config`: `quantity_tolerance`, `cash_tolerance`, `quantity_materiality`, `cash_materiality_base`,
`pending_settlement_days`, `fx_rates{CCY: rate_to_base}`.

## Citation format

`{side}:{source_ref}@{date}` — e.g. `internal:books;pos;acct=CUST-A;sec=ISIN-BBB@2026-06-26` and
`external:custodian;stmt=JUN;acct=CUST-A;sec=ISIN-BBB@2026-06-26`. Every break carries lineage
citations to the internal and/or external rows it was derived from (`internal:` / `external:`
prefix).

## Freshness / effective dates

- `config` (tolerances, materiality, pending-settlement window, fx rates) is a **versioned
  contract**; the output records `config_version` so a reconciliation is reproducible.
- `as_of` fixes the reconciliation date. **Pending-settlement** items are trades that settle after
  `as_of` within `pending_settlement_days`; they are documented reconciling items expected to clear
  at settlement, not adjusted.
- `input_fingerprint` (a content hash of the normalized inputs + config) makes the
  `reconciliation_id` a pure function of the inputs — re-running the same inputs is idempotent, and
  the `reconciliation_id` is the durable case/job id downstream skills reuse.

## Least-privilege operations (deployment)

- `books.read(entity, account, as_of)` → bounded internal positions and cash for the account.
- `custodian.read(account, as_of)` / `prime_broker.read(...)` / `administrator.read(...)` /
  `counterparty.read(...)` → bounded external holdings and cash balances.
- `config.get('pcr', version)` → tolerances, materiality, pending-settlement window, fx rates.
- `recon.get(reconciliation_id)` → prior-period open items for carry-forward.

All read-only, deterministic, durable `reconciliation_id`, below the fixed timeout; page long
histories as resumable stages. **No write/repair/move operation is bound to this skill** — proposed
reconciling items are handed to an authorized human/system to review and action in the book of
record, and order/trade breaks are routed to `trade-break-resolver`.
