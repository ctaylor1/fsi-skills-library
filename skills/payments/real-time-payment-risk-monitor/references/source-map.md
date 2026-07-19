# Source Map — real-time-payment-risk-monitor

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Risk rule library + watchlists** (versioned) | Velocity, per-transaction limit, structuring, mule, screening, and liquidity thresholds; sanctions / fraud / mule list membership | Read-only |
| 2 | **Payment gateway / processor / acquirer** (payment book of record) | Instant-payment events: direction, status, amount, counterparty, scheme, timestamp | Read-only |
| 3 | **Fraud platform** | Enrichment signals, prior flags, device / behavior context for the reviewer | Read-only |
| 4 | **Settlement** (prefunded funding positions) | Net and pending outflow vs prefunded liquidity for RTP/FedNow-style positions | Read-only |
| 5 | **Network rules / scheme reference** | Scheme identification, scheme-level caps and windows | Read-only |
| 6 | **ISO 20022 parser** | Normalize pain/pacs/camt messages into payment events and counterparties | Read-only |
| 7 | **Ledger** | Reconcile flow/liquidity figures to the cash book of record for evidence | Read-only |
| 8 | **Prior open-alert store** | Deduplication of already-open alerts across runs | Read-only |
| 9 | **Case management** | Where a human (not this monitor) opens/works/closes a case from an alert | Read-only for context |

The **rule library and watchlists are the definition of record** for every threshold and
screening entry. Never infer a limit, a watchlist entry, or a fraud/AML/sanctions
determination from the payment flow, a prior run, or an analyst's assertion. If the payment
feed and the settlement feed disagree on an amount, cite both and raise the ambiguity — do
not resolve it silently.

## Citation format

`{system}:{ref}@{as_of}` — e.g.
`payments:account=ACCT-MULE;pattern=passthrough@2026-07-17T14:30`,
`payments:account=ACCT-WATCH;payment=W-01;counterparty=CP-SANCTION-1@2026-07-17T14:30`,
`settlement:position=POS-USD-FEDNOW@2026-07-17T14:30`, and each rule cites
`rules:rule_id=VELO-CNT-20@rtp-risk-cfg-2026.07`. Every alert cites the measured evidence
row(s) and the rule (with its config version).

## Freshness / effective dates

- Thresholds and watchlists are a **versioned contract** (`config_version`); the pack records
  the version so a run is reproducible and an alert ties to the exact rule text in force.
- Each account/position carries a feed `as_of`. The monitor computes `staleness_minutes`
  against the run `as_of` and the mandate's `max_staleness_minutes`. Minutes (not days) is the
  freshness unit because instant payments settle in seconds.
- **Stale feeds are flagged, never suppressed.** A stale entity raises a freshness alert and
  every alert derived from it is marked `stale_input: true`; results are treated as
  low-confidence pending a refreshed feed, not silently dropped.

## Least-privilege operations (deployment)

- `rules.get(config_version)` → the versioned rule set and buffers.
- `watchlists.get(list_name, as_of)` → sanctions / fraud / mule membership.
- `payments.window(account_id, window_minutes, as_of)` → windowed instant-payment events.
- `settlement.positions(as_of)` → prefunded liquidity, net and pending outflow.
- `refdata.resolve(counterparty|scheme)` → normalized counterparty / scheme.
- `alerts.open(config_version)` → previously-open alert fingerprints for deduplication.

All read-only, deterministic, below the fixed timeout, with a durable `run_id`. Page large
payment windows as resumable stages. The monitor writes **nothing** back to any system of
record — it only emits alerts and queue items for human review and adjudication.
