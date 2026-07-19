# Source Map — employee-trading-preclearance-assistant

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Employee-trading / preclearance register** (system of record) | Prior decisions, open requests, clearance windows, conditions; precondition + post-state verification | Read for planning; **approval-gated write** for execute |
| 2 | **Restricted-list / watch-list registers** (controlled content library, versioned) | Restricted (hard-block) and watch/grey (soft) securities and issuers, with effective dates | Read-only |
| 3 | **Wall-cross / MNPI / insider lists + conflicts register** | Conflict and material-non-public-information flags for the employee/issuer | Read-only |
| 4 | **Employee holdings & personal-account feed** (entity resolution) | Positions, last covered-purchase dates for the minimum-holding rule, account ownership | Read-only |
| 5 | **Personal-trading policy corpus** (approved-source retrieval, versioned) | Blackout calendars, de-minimis and notional thresholds, minimum-holding period, decision-authority matrix | Read-only |
| 6 | **Permission / case-state / approval broker** | Approval-token issuance, approver-role check, execute gating, segregation of duties, audit | Controlled |

Sanctions/PEP data, transaction-monitoring, KYC/AML, case-management, and the records
archive are consumed via the shared platform services (see
[../../../../docs/SHARED-SERVICES.md](../../../../docs/SHARED-SERVICES.md)); this skill does
not reimplement them.

## Least-privilege operations (deployment)

Separate, single-purpose operations (never a combined "just clear it"):

- `preclearance.read(request_id)` / `preclearance.read_open(employee_id)` — read-only.
- `screens.evaluate(request)` → restricted/watch/blackout/min-holding/MNPI results — read-only, deterministic.
- `approval.request(plan_hash, required_role)` → token (human-in-the-loop; approver ≠ employee).
- `preclearance.record_decision(step, idempotency_key, token)` — **approval-gated, idempotent write**; rejects a missing/mismatched token or stale plan hash.
- `preclearance.issue_clearance(step, idempotency_key, token)` — issues the time-boxed clearance window; **approval-gated, idempotent**.
- `preclearance.verify(request_id, expected_post_state)` — read-only post-check.
- `preclearance.rollback(step, idempotency_key, token)` — revoke a decision/clearance step.
- `audit.record(plan_id, events)` — append-only audit.

Each operation is below the fixed timeout; multi-step execution is a **resumable staged**
process keyed by `plan_id` + step idempotency keys. No hidden retries; no step-up assumed.

## Citation / identifier format

`preclearance:{request=PCR-NNNNN};{object}@{state-read-time}`; the plan records the exact
pre-state reads and the versioned restricted-list / policy it relied on so verification and
audit are reproducible. Employee and account identifiers are masked to last 4 in citations.
