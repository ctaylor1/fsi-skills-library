# Source Map — loan-servicing-exception-resolver

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | Core-banking / **loan-servicing** (system of record) | Exception state, balances, preconditions, post-state verification | Read for planning; **approval-gated write** for execute |
| 2 | **Document-intelligence** | Payment/fee/escrow evidence | Read-only |
| 3 | Approved **calculation service** | Remedy amounts, expected post-state, escrow recomputation | Read-only |
| 4 | Permissible-remedy **catalog** + authority limits (versioned) | Remedy validity + limits + approver roles | Read-only |
| 5 | **Permission / approval broker** | Approval token issuance, role check, execute gating, audit | Controlled |

## Least-privilege operations (deployment)

Separate, single-purpose operations (never a combined "fix it"):

- `servicing.read(loan_id)` / `servicing.read_exception(exception_id)` — read-only.
- `calc.remedy(exception)` → amount + expected post-state — read-only, deterministic.
- `approval.request(plan_hash, required_role)` → token (human-in-the-loop).
- `servicing.apply(step, idempotency_key, token)` — **approval-gated, idempotent write**;
  rejects a missing/mismatched token or stale plan hash.
- `servicing.verify(loan_id, expected_post_state)` — read-only post-check.
- `servicing.rollback(step, idempotency_key, token)` — reverse a step.
- `audit.record(plan_id, events)` — append-only audit.

Each operation is below the fixed timeout; multi-step execution is a **resumable staged**
process keyed by `plan_id` + step idempotency keys. No hidden retries; no step-up assumed.

## Citation / identifier format

`servicing:{loan=****NNNN};{object}@{state-read-time}`; the plan records the exact
pre-state reads it relied on so verification and audit are reproducible.
