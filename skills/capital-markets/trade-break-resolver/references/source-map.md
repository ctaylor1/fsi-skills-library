# Source Map — trade-break-resolver

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | Firm **OMS/EMS** (system of record) | Break state, booking economics, preconditions, post-state verification | Read for planning; **approval-gated write** for execute |
| 2 | **Post-trade / clearing** + counterparty confirmation | The affirmed/confirmed "true" economics to match against | Read-only |
| 3 | **Market & reference data** | Instrument static, settlement calendars, prices | Read-only |
| 4 | **Communications archive** | Agreed-terms evidence (recorded/affirmed trade agreement) | Read-only |
| 5 | Permissible-repair **catalog** + authority limits (versioned) | Repair validity + limits + approver roles | Read-only |
| 6 | **Permission / approval broker** | Approval token issuance, role check, execute gating, audit | Controlled |

The counterparty, custodian, and CCP records are the **reference** for matching — they are
never a writable target. This skill repairs only the firm's own OMS/EMS booking.

## Least-privilege operations (deployment)

Separate, single-purpose operations (never a combined "fix it"):

- `oms.read(trade_id)` / `oms.read_break(break_id)` — read-only.
- `clearing.read(trade_id)` — read counterparty/custodian/CCP confirmation — read-only.
- `refdata.read(instrument)` — instrument static, calendars — read-only.
- `match.classify(break)` → break type + economic difference — read-only, deterministic.
- `approval.request(plan_hash, required_role)` → token (human-in-the-loop).
- `oms.apply(step, idempotency_key, token)` — **approval-gated, idempotent write** (amend /
  cancel / rebook); rejects a missing/mismatched token or stale plan hash.
- `oms.verify(trade_id, expected_post_state)` — read-only post-check.
- `oms.rollback(step, idempotency_key, token)` — reverse a step.
- `audit.record(plan_id, events)` — append-only audit.

Each operation is below the fixed timeout; multi-step execution is a **resumable staged**
process keyed by `plan_id` + step idempotency keys. No hidden retries; no step-up assumed.

## Citation / identifier format

`oms:{trade=****NNNN};{object}@{state-read-time}` and
`clearing:{confirm=****NNNN}@{read-time}`; the plan records the exact pre-state reads it
relied on so verification and audit are reproducible.
