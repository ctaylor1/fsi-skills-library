# Domain Rules — corporate-action-election-assistant

The firm's corporate-actions policy and its **permissible-election catalog** (versioned)
govern. Nothing outside the catalog may be planned or submitted by this skill. The holder
(or an authorized instruction on the account) chooses the option; this skill never
recommends **which** option to elect.

## Permissible-election catalog (default)

| Event type | Submittable options | Quantity basis | Reversible before deadline? | Notional authority limit | Approver role |
| ---------- | ------------------- | -------------- | --------------------------- | ------------------------ | ------------- |
| `tender_offer` | tender | up to eligible | Yes (withdraw before expiry) | ≤ 5,000,000 | corporate-actions-supervisor |
| `exchange_offer` | exchange | up to eligible | Yes (withdraw before expiry) | ≤ 5,000,000 | corporate-actions-supervisor |
| `dividend_option` | cash, shares | **entire** eligible position | Yes (amend before cutoff) | ≤ 1,000,000 | corporate-actions-specialist |
| `rights_subscription` | subscribe, oversubscribe | up to eligible × cap | Yes (amend before cutoff) | ≤ 2,000,000 | corporate-actions-supervisor |
| `conversion` | convert | up to eligible | Yes (rescind before cutoff) | ≤ 2,000,000 | corporate-actions-supervisor |

- **Quantity basis.** `up_to` events allow a partial election (instructed ≤ eligible). The
  `entire`-basis optional dividend must allocate the **whole** eligible holding across the
  cash/shares legs (instructed = eligible). Not electing is the default; a no-action leg
  (decline / lapse / hold) is never a submitted instruction.
- **Oversubscription.** For `rights_subscription`, the `oversubscribe` option raises the
  effective cap (default × 2.0). The instructed total still may not exceed
  eligible × effective cap; over that is out of scope.
- **Notional.** Notional = instructed quantity × reference price. Over the authority limit,
  irreversible, past the window, or off-catalog → **fail closed** and escalate to a human
  authority (corporate-actions operations / a higher approver).

## Eligibility & deadline rules

- **Eligibility is the record-date holding**, not today's position. A position `as_of`
  other than the record-date holding is surfaced, not silently used.
- Two deadlines matter: the **agent/custodian submission cutoff** (`submission_deadline`)
  and the later **market/protect deadline** (`market_deadline`). This skill plans and
  submits strictly **before the submission cutoff**. `as_of` on/after the cutoff → fail
  closed; a late/protect instruction is a manual operations decision, out of scope here.

## Plan requirements (every step / leg)

- **Idempotency key** deterministic from `{plan_id, step_id, option, quantity, account}`;
  re-submitting the same leg with the same key must be a no-op (never a double election).
- **Precondition** read from books-and-records / the agent at submission time (eligible
  covers cumulative instructed; window still open; option permissible) — checked, not
  assumed.
- **Expected effect** with an instructed quantity that ties to the leg quantity; the leg
  quantities tie to `instructed_quantity`.
- **Verification** that reads the custodian/agent acknowledgment after submission and
  compares option + quantity to the plan.
- **Rollback** = withdraw or supersede the leg before the deadline. If an event cannot be
  amended/withdrawn before the deadline it is **not reversible** and is out of scope.

## Approval binding

- Approval yields a **token** bound to the **plan hash** and the approver's **role**.
- Any change to the plan after approval changes the hash and **voids** the token.
- Submission is permitted **only** with a valid token whose role matches the plan's required
  approver role and whose notional is within the authority limit.

## Post-submission verification & rollback

- Verify the **actual** acknowledgment (read the custodian/agent) equals the intended
  election (event, account, option, quantity). On mismatch, **withdraw/supersede** the leg
  before the deadline and halt; never continue on a mismatch.
- On partial completion, roll the submitted legs back (before the deadline) so the account
  is never left with a half-submitted election that does not reflect the approved plan.
