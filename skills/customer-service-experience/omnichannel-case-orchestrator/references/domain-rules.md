# Domain Rules — omnichannel-case-orchestrator

The firm's customer-service policy and its **permissible-action catalog** (versioned)
govern. Nothing outside the catalog may be planned or executed by this skill. Product terms
and the goodwill matrix are versioned contracts consulted for eligibility.

## Permissible-action catalog (default)

| Action type | Action | Evidence required | Monetary? | Reversible? | Authority limit | Approver role |
| ----------- | ------ | ----------------- | --------- | ----------- | --------------- | ------------- |
| `fee_adjustment` | `waive_fee` (waive/refund a fee assessed in error or by courtesy) | fee record + eligibility per product terms | Yes | Yes (re-assess) | ≤ 250 | case-supervisor |
| `goodwill_credit` | `issue_goodwill_credit` (service-recovery credit) | goodwill matrix ref + reason code | Yes | Yes (reverse credit) | ≤ 100 | case-supervisor |
| `billing_refund` | `refund_overcharge` (return a confirmed overcharge) | billing record + overcharge evidence | Yes | Yes (reclaim/void) | ≤ 500 | case-supervisor |
| `account_change` | `update_contact_preference` (change a non-financial account setting) | verified identity + customer request | No | Yes (restore prior value) | 0 (no money) | account-specialist |
| `outbound_commitment` | `send_resolution_confirmation` (approved outbound message) | approved template id + customer consent | No | Yes (correction/retraction) | 0 (no money) | qa-reviewer |

- **Plan authority cap:** total monetary exposure across all actions in one plan ≤ **1,000**.
- Actions not listed, over a per-action limit, over the plan cap, irreversible, or requiring
  a policy exception are **out of scope** — fail closed and escalate to a human authority.
- Non-monetary actions (account changes, outbound commitments) still require human approval
  because they change an account or make a customer-facing commitment.

## Approver role seniority

`case-agent` (1) < `qa-reviewer` (2) = `account-specialist` (2) < `case-supervisor` (3).
The plan's `required_role` is the **most senior** role across all its actions. A plan that
mixes a fee waiver and an account change requires `case-supervisor` approval.

## Plan requirements (every step)

- **Idempotency key** deterministic from `{plan_id, action_id, action, amount, target}`;
  re-running a step with the same key must be a no-op (no double refund, no duplicate
  outbound message).
- **Precondition** read from the relevant system of record (e.g., "fee still assessed",
  "identity verified", "consent on file") — checked at execute time, not assumed.
- **Expected effect** with amounts that tie to the action amount (monetary actions).
- **Verification** that reads the system of record after the step and compares to expected.
- **Rollback** method that returns that system to the last verified state.

## Approval binding

- Approval yields a **token** bound to the **plan hash** and the approver's **role**.
- Any change to the plan after approval changes the hash and **voids** the token.
- Execution is permitted **only** with a valid token whose `approver_role` equals the plan's
  `required_role` and whose amounts are within the authority limits and plan cap.

## Post-state verification & rollback

- Verify the **actual** post-state (read case/CRM/billing/comms) equals the expected
  post-state. On mismatch, **roll back** the step and halt; never continue on a mismatch.
- On partial completion across systems, roll back to the last verified checkpoint so the
  customer is never left with a half-applied resolution (e.g., a refund posted but the
  confirmation never sent, or a preference changed but the fee not waived).
