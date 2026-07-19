# Domain Rules — employee-trading-preclearance-assistant

The firm's **personal-trading policy** (versioned) and its restricted/watch lists, blackout
calendars, and decision-authority matrix govern. Nothing outside this ruleset may be planned
or executed. All thresholds below are defaults; deployment supplies the versioned policy.

## Mandatory screens (input)

A preclearance request cannot be planned unless **all** of these screens were performed and
returned an explicit boolean result (`scripts/validate_input.py` fails closed otherwise):

| Screen | Field | Meaning |
| ------ | ----- | ------- |
| `restricted_list` | `hit` | Issuer/security on the firm restricted list |
| `watch_list` | `hit` | Issuer/security on the watch (grey) list |
| `blackout` | `active` | Employee inside an active blackout / quiet period |
| `min_holding_period` | `breach` | Sell would breach the minimum-holding rule |
| `conflicts_mnpi` | `flag` | Employee flagged for a conflict or possession of MNPI |

## Hard blocks (decision must be `deny`)

Any of the following forces a `deny` decision. The builder can **never** emit an `approve*`
plan when a hard block is present, and `validate_output` rejects one that claims to:

- `restricted_list.hit == true`
- `blackout.active == true`
- `min_holding_period.breach == true` (default minimum-holding period: **30 days**)
- `conflicts_mnpi.flag == true` (also route to surveillance/conflicts — see handoffs)

## Decision matrix (deterministic)

| Condition (no hard block) | Decision | Required approver role | Notional authority limit |
| ------------------------- | -------- | ---------------------- | ------------------------ |
| `watch_list.hit` OR notional > 100,000 | `approve_with_conditions` | `compliance-officer` | ≤ 1,000,000 |
| otherwise | `approve` | `compliance-preclearance-analyst` | ≤ 100,000 |
| any hard block | `deny` | `compliance-officer` | n/a |
| notional > 1,000,000 | **REJECTED** (escalate to CCO) | Chief Compliance Officer | out of scope |

Conditions attached to an approval: a **buy** always records a `min_holding_lock:30d`
condition (so a subsequent sell within the window is caught by the min-holding screen); a
`watch_list` hit adds `watch_list_monitoring`.

## Clearance window

An approval issues a **time-boxed** clearance (`valid_from` = request date, `valid_to` = next
trading day). The clearance authorizes the requested instrument, side, and **up to** the
requested notional only. It is not a standing authorization and expires unused.

## Plan requirements (every step)

- **Idempotency key** deterministic from `{plan_id, step_id, action, post_state}`; re-running a
  step with the same key must be a no-op.
- **Precondition** read from the preclearance register (e.g., "no prior open decision",
  "decision recorded", "clearance window active") — checked at execute time, not assumed.
- **Expected effect** and a **post-state** contribution that ties to the decision (an approve*
  plan clears the exact notional; a deny plan issues no clearance).
- **Verification** that reads the register after the step and compares to expected.
- **Rollback** that voids the decision, revokes the clearance, or removes conditions.

## Approval binding

- Approval yields a **token** bound to the **plan hash** and the approver's **role**.
- Any change to the plan (decision, notional, steps) after approval changes the hash and
  **voids** the token.
- Execution is permitted **only** with a valid token whose role matches the plan's required
  approver role, whose notional is within the authority limit, and whose **approver is not the
  requesting employee** (segregation of duties).
