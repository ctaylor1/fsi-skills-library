# Domain Rules — accounts-payable-exception-resolver

The firm's accounts-payable policy and its **permissible-remedy catalog** (versioned)
govern. Nothing outside the catalog may be planned or executed by this skill, and **no
remedy disburses funds or changes supplier banking details**.

## Permissible-remedy catalog (default)

| Exception type | Remedy action | Evidence required | Reversible? | Authority limit | Approver role |
| -------------- | ------------- | ----------------- | ----------- | --------------- | ------------- |
| `invoice_price_variance` | `adjust_invoice_price` (move variance from AP liability to price-variance account) | Invoice + PO + price-variance evidence | Yes (reverse the adjustment) | ≤ 5,000 | ap-supervisor |
| `po_quantity_variance` | `align_to_po_quantity` (move over-billed value from AP liability to GR/IR clearing) | Invoice + PO + receipt | Yes (restore prior match) | ≤ 5,000 | ap-supervisor |
| `receipt_mismatch` | `match_to_receipt` (hold unreceived value in GR/IR pending goods receipt) | Invoice + receipt | Yes (restore prior match) | ≤ 5,000 | ap-supervisor |
| `duplicate_invoice` | `block_duplicate` (place a payment hold and flag the duplicate) | Both invoice records + duplication proof | Yes (release hold / unflag) | ≤ 50,000 | ap-manager |
| `tax_miscode` | `correct_tax_code` (correct tax code and recompute; offset AP liability) | Invoice + tax determination | Yes (restore prior tax code) | ≤ 2,000 | tax-analyst |
| `bank_detail_mismatch` | `hold_for_bank_verification` (protective payment hold pending supplier bank re-verification) | Invoice + supplier bank master + bank-change request | Yes (release hold after verification) | ≤ 250,000 | ap-manager |
| `approval_missing` | `route_for_approval` (place an approval hold and route per delegation of authority) | Invoice + PO + delegation-of-authority | Yes (recall routing) | ≤ 250,000 | ap-supervisor |

The **amount** is the correction/protected value: for `adjust_invoice_price`,
`align_to_po_quantity`, `match_to_receipt`, and `correct_tax_code` it is the money-value
delta corrected; for `block_duplicate`, `hold_for_bank_verification`, and
`route_for_approval` it is the invoice value placed under hold/routing (no funds move). The
hold/routing limits are higher because a **hold is protective** — placing one is the safe
direction; releasing one is not a remedy this skill performs.

Remedies not listed, over the authority limit, irreversible, requiring a disbursement or a
bank-master change, or requiring a policy exception are **out of scope** — fail closed and
escalate to a human authority.

## Plan requirements (every step)

- **Idempotency key** deterministic from `{plan_id, step_id, action, amount, target}`;
  re-running a step with the same key must be a no-op.
- **Precondition** read from the AP subledger (e.g., "GR/IR holds the variance", "invoice
  not yet paid", "hold not already placed") — checked at execute time, not assumed.
- **Expected effect** with amounts that tie to the remedy amount.
- **Verification** that reads the system of record after the step and compares to expected.
- **Rollback** method that returns the invoice to the last verified state.

## Approval binding

- Approval yields a **token** bound to the **plan hash** and the approver's **role**.
- Any change to the plan after approval changes the hash and **voids** the token.
- Execution is permitted **only** with a valid token whose role matches the plan's required
  approver role and whose amount is within the authority limit.

## Post-state verification & rollback

- Verify the **actual** post-state (read the AP subledger) equals the expected post-state.
  On mismatch, **roll back** the step and halt; never continue on a mismatch.
- On partial completion, roll back to the last verified checkpoint so the invoice is never
  left half-corrected.
