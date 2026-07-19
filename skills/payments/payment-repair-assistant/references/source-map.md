# Source Map — payment-repair-assistant

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Payment-operations / rail-connectivity** (system of record) | Payment status, hold/reject state, preconditions, post-state verification, submit/return/release | Read for planning; **approval-gated write** for execute |
| 2 | **ISO 20022 message store** + document-intelligence | Original pain/pacs/camt message, invalid/missing fields, repair evidence | Read-only |
| 3 | **Sanctions / screening service** | Screening status and cleared disposition for the payment/parties | Read-only |
| 4 | **Entity resolution** (beneficiary) | Confirm beneficiary name, account, BIC/IBAN against the directory | Read-only |
| 5 | Permissible-repair **catalog** + authority limits (versioned) | Repair validity + limits + approver roles | Read-only |
| 6 | **Permission / approval broker** | Approval token issuance, role check, execute gating, audit | Controlled |

## Least-privilege operations (deployment)

Separate, single-purpose operations (never a combined "just fix and send it"):

- `payops.read(payment_id)` / `payops.read_case(case_id)` — read-only.
- `iso20022.read(message_id)` / `screening.read(payment_id)` — read-only.
- `entity.resolve_beneficiary(...)` — read-only confirmation.
- `approval.request(plan_hash, required_role)` → token (human-in-the-loop).
- `payops.apply_repair(step, idempotency_key, token)` — **approval-gated, idempotent write**;
  rejects a missing/mismatched token or stale plan hash.
- `payops.resubmit(step, end_to_end_id, idempotency_key, token)` — **approval-gated,
  idempotent** submission; rejects a duplicate for the same end-to-end id.
- `payops.release(step, idempotency_key, token)` / `payops.return(step, idempotency_key,
  token)` — approval-gated, idempotent.
- `payops.verify(payment_id, expected_post_state)` — read-only post-check.
- `payops.rollback(step, idempotency_key, token)` — recall/return (camt.056), re-hold, or
  restore a field.
- `audit.record(plan_id, events)` — append-only audit.

Each operation is below the fixed timeout; multi-step execution is a **resumable staged**
process keyed by `plan_id` + step idempotency keys (each bound to the payment's
end-to-end id). No hidden retries; no step-up assumed.

## Citation / identifier format

`payops:{payment=****NNNN};{e2e=E2E-...};{object}@{state-read-time}`; the plan records the
exact pre-state reads (payment status, screening disposition, message fields) it relied on so
verification and audit are reproducible.
