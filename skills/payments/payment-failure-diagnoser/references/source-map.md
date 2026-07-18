# Source Map — payment-failure-diagnoser

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Processor / scheme trace** (gateway, processor, acquirer, CSM) | The ordered lifecycle legs and each leg's status/reason code | Read-only |
| 2 | **Settlement / ledger** record | Whether value actually moved (debit/credit/return), duplicate detection | Read-only |
| 3 | **Network-rules / code-set** reference (ISO 8583, NACHA, ISO 20022 external code sets) | Resolving each reason code's meaning and category | Read-only |
| 4 | **ISO 20022 parser** | Message-type and status-reason extraction for pacs/pain/camt legs | Read-only |
| 5 | Payments-strategy **config** (versioned) | Root-cause → route mapping and retry-eligibility policy | Read-only |

Never substitute a customer or merchant assertion for the scheme/settlement record. If the
scheme trace and the settlement/ledger record conflict (e.g. `RJCT` but a posted debit),
cite both and route to investigation — do not resolve silently.

## Citation format

`{system}:{ref}@{timestamp}` — e.g. `scheme:pmt=****9001;leg=4;msg=pacs.002@2026-07-15T09:12:00`.
Every interpreted leg cites its `source_ref`; the decisive (root-cause) leg is cited in the
root-cause block.

## Freshness / effective dates

- The **code set** (ISO 8583 / NACHA / ISO 20022 external codes) and the root-cause→route
  **config** are **versioned contracts**; the diagnosis records the versions used so it is
  reproducible.
- A trace is only as current as its terminal leg; state the `as_of` and whether the trace is
  complete or still in flight.

## Least-privilege operations (deployment)

- `scheme.trace(payment_id)` → ordered legs with stage/status/reason_code/timestamp/source_ref.
- `settlement.status(payment_id)` → posted debit/credit/return and value-moved flag.
- `codeset.resolve(rail, code, version)` → meaning + category for a reason code.
- `iso20022.extract(message_ref)` → message type + `TxSts` + status-reason code(s).
- `config.get('payment_routing', version)` → root-cause→route + retry policy.

All read-only, deterministic, durable `diagnosis_id`, below the fixed timeout; page long
traces as resumable stages. No operation modifies, resubmits, reverses, releases, or cancels
a payment — those are downstream, approval-gated skills.
