# Domain Rules — trade-break-resolver

The firm's trade-support policy and its **permissible-repair catalog** (versioned) govern.
Nothing outside the catalog may be planned or executed by this skill. All repairs act on the
firm's own OMS/EMS booking only — never the counterparty, custodian, or CCP record.

## Break taxonomy → permissible-repair catalog (default)

| Break type | Repair action | Evidence required | Reversible? | Authority limit (economic value) | Approver role |
| ---------- | ------------- | ----------------- | ----------- | -------------------------------- | ------------- |
| `mis_booked_account` | `rebook_trade` (cancel on wrong book → rebook on correct book) | Firm booking + counterparty confirmation + correct booking target | Yes (rebook to prior book) | ≤ 5,000,000 notional | trade-support-supervisor |
| `quantity_mismatch` | `amend_quantity` (correct traded quantity to the confirmed value) | Firm booking + counterparty confirmation + matched trade key | Yes (re-amend to prior qty) | ≤ 5,000,000 notional | trade-support-supervisor |
| `price_mismatch` | `amend_price` (correct price / settlement amount to the agreed value) | Firm booking + counterparty confirmation + agreed-price evidence | Yes (re-amend to prior price) | ≤ 250,000 economic difference | trade-support-specialist |
| `duplicate_booking` | `cancel_trade` (cancel the duplicate booking) | Both firm bookings + duplication proof | Yes (rebook the cancelled trade) | ≤ 5,000,000 notional | trade-support-supervisor |

`amount` is the economic value of the repair: the notional moved (rebook), the notional value
of the quantity correction (amend_quantity), the economic difference (amend_price), or the
notional of the duplicate booking (cancel_trade). Repairs not listed, over the authority limit,
irreversible, or requiring a policy exception are **out of scope** — fail closed and escalate
to a human authority (desk supervisor / trade control).

## Plan requirements (every step)

- **Idempotency key** deterministic from `{plan_id, step_id, action, amount, target}`;
  re-running a step with the same key must be a no-op.
- **Precondition** read from the OMS/EMS (e.g., "trade is booked to the wrong book", "duplicate
  booking still exists") — checked at execute time, not assumed.
- **Expected effect** with amounts that tie to the repair amount.
- **Verification** that reads the system of record after the step and compares to expected.
- **Rollback** method that returns the trade to the last verified state.

## Approval binding

- Approval yields a **token** bound to the **plan hash** and the approver's **role**.
- Any change to the plan after approval changes the hash and **voids** the token.
- Execution is permitted **only** with a valid token whose role matches the plan's required
  approver role and whose amount is within the authority limit.

## Post-state verification & rollback

- Verify the **actual** post-state (read the OMS/EMS) equals the expected post-state. On
  mismatch, **roll back** the step and halt; never continue on a mismatch.
- On partial completion, roll back to the last verified checkpoint so the trade is never left
  half-repaired (e.g., cancelled on the source book but not rebooked on the target).
