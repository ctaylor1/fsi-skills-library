# Source Map — account-anomaly-screener

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | Core-banking **transactions** (position of record) | Focal activity + baseline history | Read-only |
| 2 | **CRM** customer context | Travel notices, life events, known payees, prior contact | Read-only |
| 3 | **Reference data** | Merchant/counterparty resolution, geo normalization, channel taxonomy | Read-only |
| 4 | Fraud-strategy **config** (versioned) | Signal thresholds and priority mapping | Read-only |

Never substitute a customer assertion for the transaction record. If the transaction record
and a statement/CRM note conflict, cite both and flag for the reviewer.

## Citation format

`{system}:{ref}@{date}` — e.g. `txns:acct=****1234;txnid=T-88213@2026-07-10`. Every fired
signal cites the specific evidence rows and the baseline window used.

## Freshness / effective dates

- Config (thresholds, mapping) is a **versioned contract**; the output records the config
  version used so a screening is reproducible.
- Baseline lookback default 180 days; state the exact window in the output.
- Exclude the focal transactions from the baseline to avoid self-contamination.

## Least-privilege operations (deployment)

- `txns.read(account_id, from, to)` → bounded, paged transaction rows.
- `crm.context(account_id)` → travel notices, known payees, flags (no free-text PII beyond
  what evidences a signal).
- `refdata.resolve(merchant|geo|channel)` → normalized values.
- `config.get('anomaly', version)` → thresholds + mapping.
All read-only, deterministic, durable `screening_id`, below the fixed timeout; page long
histories as resumable stages.
