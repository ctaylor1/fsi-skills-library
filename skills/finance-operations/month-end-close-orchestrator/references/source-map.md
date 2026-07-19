# Source Map — month-end-close-orchestrator

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **ERP / general ledger** (system of record) | Period status, account postability, journal posting, post-state verification | Read for planning; **approval-gated write** for execute |
| 2 | **Subledgers** (AP, AR, fixed assets, inventory, payroll) | Sub-ledger tie-out, lock state, exception status | Read for planning; approval-gated **lock** for execute |
| 3 | **Close-task / certification system** | Task graph, dependencies, sign-off state, reconciliation certifications | Read for planning; approval-gated **certify** for execute |
| 4 | **Reconciliation platform** | Reconciliation status and unresolved-break counts | Read-only |
| 5 | **Consolidation / FP&A / regulatory reporting** | Downstream consumers of the closed period (packaging, not gated here) | Read-only |
| 6 | Permissible **close-action catalog** + posting-authority limits (versioned) | Action validity, limits, approver roles | Read-only |
| 7 | **Permission / approval broker** | Approval-token issuance, role check, execute gating, audit | Controlled |
| 8 | **Document / spreadsheet intelligence** | Support schedules, allocation bases, reconciliation evidence | Read-only |

The ERP/GL is authoritative for balances and period state; the close-task system is
authoritative for task dependencies and certifications. On conflict, the system of record for
the specific object wins, and the discrepancy is surfaced rather than reconciled silently.

## Least-privilege operations (deployment)

Separate, single-purpose operations (never a combined "close it"):

- `gl.read(period, account)` / `close.read_run(close_run_id)` — read-only state.
- `recon.read(recon_id)` → status + unresolved-break count — read-only.
- `plan.build(close_run)` → validated, blocked/pending plan — deterministic, no writes.
- `approval.request(plan_hash, required_role)` → token (human-in-the-loop).
- `gl.post(step, idempotency_key, token)` — **approval-gated, idempotent** journal post.
- `close.certify(step, idempotency_key, token)` — approval-gated certification sign-off.
- `subledger.lock(step, idempotency_key, token)` / `period.close(step, idempotency_key, token)`
  — approval-gated state change.
- `*.verify(target, expected_post_state)` — read-only post-check.
- `*.rollback(step, idempotency_key, token)` — reverse a posted journal, rescind a sign-off,
  or re-open a locked sub-ledger/period.
- `audit.record(plan_id, events)` — append-only audit.

Each operation is below the fixed timeout; multi-step execution is a **resumable staged**
process keyed by `plan_id` + per-step idempotency keys. No hidden retries; no step-up assumed.

## Citation / identifier format

`gl:{entity};{period};{account}@{state-read-time}` and
`close:{close_run_id};{task_id}@{read-time}`; the plan records the exact pre-state reads it
relied on so verification and audit are reproducible.
