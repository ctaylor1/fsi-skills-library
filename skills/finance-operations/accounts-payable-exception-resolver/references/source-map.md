# Source Map — accounts-payable-exception-resolver

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | ERP **AP subledger** (system of record) | Invoice/match state, balances, preconditions, post-state verification | Read for planning; **approval-gated write** for execute |
| 2 | **Procurement / PO** system | Purchase-order price, quantity, and terms | Read-only |
| 3 | **Goods-receipt** system (GRN) | Received quantity/value for three-way match | Read-only |
| 4 | **Document-intelligence** | Invoice extraction, tax determination, duplicate/bank-change evidence | Read-only |
| 5 | Approved **calculation service** | Remedy amounts, variance, tax recomputation, expected post-state | Read-only |
| 6 | Permissible-remedy **catalog** + authority limits (versioned) | Remedy validity + limits + approver roles | Read-only |
| 7 | **Permission / approval broker** | Approval token issuance, role check, execute gating, audit | Controlled |

The **supplier bank master** is read-only evidence for a bank-detail mismatch only. This
skill never writes it; a bank-master change is a separate vendor-master control.

## Least-privilege operations (deployment)

Separate, single-purpose operations (never a combined "fix and pay it"):

- `ap.read(invoice_id)` / `ap.read_exception(exception_id)` — read-only.
- `po.read(po_id)` / `grn.read(receipt_id)` — read-only match evidence.
- `calc.remedy(exception)` → amount + expected post-state — read-only, deterministic.
- `approval.request(plan_hash, required_role)` → token (human-in-the-loop).
- `ap.apply(step, idempotency_key, token)` — **approval-gated, idempotent write** to the AP
  subledger (match/tax/hold-state only); rejects a missing/mismatched token or stale plan
  hash. **Not** a disbursement operation.
- `ap.verify(invoice_id, expected_post_state)` — read-only post-check.
- `ap.rollback(step, idempotency_key, token)` — reverse a step.
- `audit.record(plan_id, events)` — append-only audit.

No `payment.disburse`, `payment_run.release`, or `vendor.update_bank` operation is bound to
this skill by design. Each operation is below the fixed timeout; multi-step execution is a
**resumable staged** process keyed by `plan_id` + step idempotency keys. No hidden retries;
no step-up assumed.

## Citation / identifier format

`ap:{vendor=****NNNN};{invoice=****NNNN};{object}@{state-read-time}`; the plan records the
exact pre-state reads it relied on so verification and audit are reproducible.
