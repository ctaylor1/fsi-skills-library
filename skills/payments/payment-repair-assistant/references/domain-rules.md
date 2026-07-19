# Domain Rules — payment-repair-assistant

The firm's payments policy and its **permissible-repair catalog** (versioned) govern. Nothing
outside the catalog may be planned or executed by this skill. Amounts are the payment value;
authority limits apply to that value in the settlement currency.

## Permissible-repair catalog (default)

| Exception type | Repair action | Evidence required | Screening required | Reversible? | Authority limit | Approver role |
| -------------- | ------------- | ----------------- | ------------------ | ----------- | --------------- | ------------- |
| `invalid_beneficiary_detail` | `repair_and_resubmit` (correct beneficiary field, resubmit) | original_message, corrected_field, verification_source | Yes | Yes (recall/return before settlement) | ≤ 100,000 | payments-repair-supervisor |
| `missing_remittance_info` | `repair_and_resubmit` (add/correct remittance info) | original_message, remittance_source | Yes | Yes | ≤ 50,000 | payments-repair-specialist |
| `missing_purpose_code` | `repair_and_resubmit` (add/correct purpose code) | original_message, purpose_code_source | Yes | Yes | ≤ 50,000 | payments-repair-specialist |
| `held_screening_cleared` | `release_and_resubmit` (release a screening-cleared hold, resubmit) | original_message, screening_disposition | Yes | Yes (re-hold) | ≤ 100,000 | payments-repair-supervisor |
| `unrecoverable_reject` | `return_to_originator` (return via pacs.004) | original_message, reject_reason | No | Yes (re-initiate) | ≤ 100,000 | payments-repair-supervisor |

Repairs not listed, over the authority limit, irreversible, or requiring a policy exception
are **out of scope** — fail closed and escalate to a human authority.

## Compliance (sanctions screening) gate

- For any repair whose action resubmits or releases the payment (`repair_and_resubmit`,
  `release_and_resubmit`), the case must carry a **cleared** screening disposition —
  `screening.status ∈ {clear, false_positive_cleared}`.
- An uncleared **hit** or a **pending** disposition **blocks** the plan. This skill does not
  adjudicate screening; route to sanctions/compliance.
- `return_to_originator` returns funds to the original debtor and does not require a new
  screening clearance, but must carry the reject reason evidence.

## Plan requirements (every step)

- **Idempotency key** deterministic from `{plan_id, step_id, action, amount, ref}`, where
  `ref` for a payment-movement step is the payment's **end-to-end id**; re-running the step
  with the same key must be a no-op (no duplicate payment).
- **Precondition** read from the payment-operations system (e.g., "payment is held in the
  repair queue", "not already resubmitted") — checked at execute time, not assumed.
- **Expected effect** with amounts that tie to the repair amount.
- **Verification** that reads the system of record after the step and confirms the status
  and that **exactly one** submission/return occurred.
- **Rollback** method that returns the payment to the last verified state (recall/return via
  camt.056, re-hold, or restore the original field).

## Approval binding

- Approval yields a **token** bound to the **plan hash** and the approver's **role**.
- Any change to the plan after approval (amount, beneficiary, target) changes the hash and
  **voids** the token.
- Execution is permitted **only** with a valid token whose role matches the plan's required
  approver role and whose amount is within the authority limit.

## Post-state verification & rollback

- Verify the **actual** payment status (read the payment-operations system) equals the
  expected post-state and that no duplicate exists for the end-to-end id. On mismatch or a
  suspected duplicate, **roll back** and halt; never continue.
- On partial completion, roll back to the last verified checkpoint so the payment is never
  left half-repaired or ambiguously double-submitted.
