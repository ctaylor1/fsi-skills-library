# Source Map — corporate-action-election-assistant

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | Depository / transfer-or-paying-**agent official notice** (post-trade/clearing) | Event terms, options, record date, submission cutoff | Read-only |
| 2 | Issuer **offering document / announcement** (offer to purchase, prospectus, 8-K) | Governing terms, oversubscription/proration terms | Read-only |
| 3 | **Portfolio-accounting / custody** (books-and-records) | Eligible record-date position; post-submission position | Read for planning; verification read |
| 4 | **Market / reference data** | Reference price for notional; security identity scrub | Read-only |
| 5 | Permissible-election **catalog** + authority limits (versioned) | Option validity, basis, caps, limits, approver roles | Read-only |
| 6 | **Custodian / agent election gateway** (post-trade/clearing) | Election submission, acknowledgment, withdrawal | **Approval-gated write** for submit |
| 7 | **Permission / approval broker** | Approval token issuance, role check, submission gating, audit | Controlled |

An upstream `corporate-action-interpreter` output (a normalized interpretation with an
`interpretation_id`) may seed the event terms, but the **official notice remains
authoritative** — never let an interpretation or a user assertion override it.

## Least-privilege operations (deployment)

Separate, single-purpose operations (never a combined "just elect it"):

- `ca.read_event(event_id)` / `custody.read_position(account, as_of)` — read-only.
- `refdata.price(security, as_of)` → reference price — read-only.
- `catalog.constraints(event_type)` → options, basis, cap, limit, approver — read-only.
- `approval.request(plan_hash, required_role)` → token (human-in-the-loop).
- `election.submit(step, idempotency_key, token)` — **approval-gated, idempotent write**;
  rejects a missing/mismatched token, stale plan hash, or a submission past the cutoff.
- `election.verify(event_id, account, expected_legs)` — read-only acknowledgment check.
- `election.withdraw(step, idempotency_key, token)` — reverse/supersede a leg before deadline.
- `audit.record(plan_id, events)` — append-only audit.

Each operation is below the fixed timeout; multi-leg submission is a **resumable staged**
process keyed by `plan_id` + step idempotency keys. No hidden retries; no step-up assumed.

## Citation / identifier format

`agent:{event=CAEV-NNNNN};{term}@{notice-version}` for terms;
`custody:{account=****NNNN};position@{as-of}` for the eligible position. The plan records
the exact reads it relied on so verification and audit are reproducible.
