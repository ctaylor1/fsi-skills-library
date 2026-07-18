# Source Map — cashflow-forecaster

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | Core-banking **transactions & balances** (position of record) | History spread, recurring inflow/outflow, opening balance | Read-only |
| 2 | **Product terms** / loan origination & servicing | Scheduled loan payments, fees, rate resets that belong in the forecast | Read-only |
| 3 | **CRM** customer context | Known recurring payees, stated one-off events (relocation, large purchase) | Read-only |
| 4 | **Document intelligence** | Extract amounts/dates from a user-provided pay stub, lease, or invoice used as an assumption | Read-only |
| 5 | Forecast **config** (versioned) | Scenario factors, volatility method, tolerance | Read-only |

The transaction/balance record is authoritative for what actually happened. A user
assumption never overrides history for the *historical* window — it only drives the *future*
periods, and it is tagged `user-supplied` so its provenance is explicit.

## Assumption provenance (required)

Every value that feeds the forecast is one of:

- `derived-from-history` — computed deterministically from the transaction record
  (`avg_inflow`, `avg_outflow`, `net_volatility`, recurring series). Reproducible from source.
- `user-supplied` — a one-off the user or an approved document asserts (a bonus per an
  employer letter, a planned tax payment, a lease change). Carries an `id`, `offset`,
  `amount`, `direction`, and where possible a document citation.

`scripts/validate_output.py` fails closed if any register entry lacks a provenance tag.

## Citation format

`{system}:{ref}@{date}` — e.g. `txns:acct=****4321;txnid=T-3002@2026-03-15`, or
`doc:employer-letter-2026.pdf#p1@2026-06-30` for a document-sourced assumption. Recurring
levels cite the history window (`as_of`, lookback) they were derived from.

## Freshness / reproducibility

- Scenario factors, the volatility method, and tolerance are a **versioned config contract**;
  the output records `config_version` so a forecast is reproducible.
- The output records the exact history window and the opening balance as-of date.
- `forecast_id` binds the output to the inputs + assumptions + config version. Re-running
  the same inputs and config reproduces every scenario and tie-out.

## Least-privilege operations (deployment)

- `txns.read(entity_id, from, to)` → bounded, paged transaction rows + opening balance.
- `product.terms(entity_id)` → scheduled obligations (loan payments, fees).
- `crm.context(entity_id)` → known payees and stated one-off events.
- `docintel.extract(document)` → amount/date fields for a user-supplied assumption.
- `config.get('cashflow', version)` → scenario factors + tolerance.

All read-only, deterministic, durable `forecast_id`, below the fixed timeout; page long
histories as resumable stages. No write path exists in this skill.
