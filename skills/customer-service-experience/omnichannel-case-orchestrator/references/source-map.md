# Source Map — omnichannel-case-orchestrator

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Case management** (system of record for the case) | Case state, durable `case_id`, chronology, action outcomes, post-state verification | Read for planning; **approval-gated write** for execute |
| 2 | **CRM / customer master** | Unified customer profile, account, verified identity, prior preference values | Read for planning; **approval-gated write** for account changes |
| 3 | **Billing / ledger** | Fee/charge records, balances, refund/credit posting and verification | Read for planning; **approval-gated write** for monetary actions |
| 4 | **Contact-center transcripts + interaction history** | Cross-channel history (phone, chat, email, IVR), consent, what the customer requested | Read-only |
| 5 | **Complaint system** | Linked complaint records, regulatory clocks, resolution obligations | Read-only for planning |
| 6 | Approved **knowledge** + **product terms** (versioned) | Eligibility, waiver/goodwill rules, approved outbound templates | Read-only |
| 7 | Permissible-action **catalog** + authority limits (versioned) | Action validity, per-action limits, plan cap, approver roles | Read-only |
| 8 | **Communication / outbound** service | Sending an approved confirmation (email/SMS/letter) | **Approval-gated write** |
| 9 | **Permission / approval broker** | Approval token issuance, role check, execute gating, audit | Controlled |

When sources conflict, the **case management** record and the **billing ledger** are
authoritative for state; the **versioned catalog + product terms** are authoritative for
what is permissible. Record the exact read time and version used so verification and audit
are reproducible.

## Least-privilege operations (deployment)

Separate, single-purpose operations (never a combined "resolve it"):

- `case.read(case_id)` / `crm.read(customer_id)` / `billing.read(account_id)` — read-only.
- `history.read(customer_id)` — unified cross-channel history — read-only.
- `catalog.read()` → permissible actions, limits, plan cap, approver roles — read-only.
- `approval.request(plan_hash, required_role)` → token (human-in-the-loop).
- `billing.apply(step, idempotency_key, token)` — **approval-gated, idempotent write**
  (fee waiver, goodwill credit, refund); rejects a missing/mismatched token or stale hash.
- `crm.apply(step, idempotency_key, token)` — **approval-gated, idempotent** account change.
- `comms.send(step, idempotency_key, token)` — **approval-gated, idempotent** outbound
  commitment against an approved template.
- `case.verify(case_id, expected_post_state)` — read-only post-check across systems.
- `case.rollback(step, idempotency_key, token)` — reverse a step to the last checkpoint.
- `audit.record(plan_id, events)` — append-only audit.

Each operation stays below the fixed timeout; multi-system execution is a **resumable
staged** process keyed by `plan_id` + step idempotency keys. No hidden retries; no step-up
authorization assumed. Treat the catalog, product terms, and approved templates as
**versioned contracts**.

## Citation / identifier format

`case:{id=CASE-NNNNN}` + `crm:{cust=****NNNN}` + `billing:{acct=****NNNN};{object}@{read-time}`;
the plan records the exact pre-state reads it relied on across each system so verification
and audit are reproducible.
