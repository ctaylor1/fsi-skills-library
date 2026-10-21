# Employee Trading Preclearance Assistant — Phase 1 method

- Require employee/account/trade identity, policy version and source, explicit institutional limits/roles/holding period, and all five mandatory screen results. There are no universal monetary or 30-day holding defaults.
- Screen records must identify the same account and include source, snapshot ID and an offset-aware timestamp. Future or stale records fail validation under the supplied policy age limit. Human reviewers must refresh restrictions and eligibility again before any operational decision.
- A supplied hard-block result produces a deny recommendation. Watch-list or higher notional routes to senior review; above the supplied senior limit produces escalation. No recommendation is a clearance.
- A proposed window ends at the next session in a supplied versioned calendar with timezone and declared complete coverage. No calendar-day increment is described as a trading day. Source/calendar truth still requires review.
- The complete original input affects `input_hash` and `plan_hash`, including account, policy, all screen snapshots, timestamps and calendar. Any change requires a new review plan; supplied approval fields cannot authorize execution.
- Output is `status=review-plan`, `action_mode=plan-only`, pending human review and `execution.state=unsupported`. No executable steps, notification, register write or rollback guarantee is generated.

## Supplied schema

Request/employee/account/instrument, side, finite positive quantity/notional, request date and offset-aware time, explicit institution policy, account-specific screening snapshots, and supplied calendar sessions/coverage/timezone. `price` if supplied is retained in the source hash; notional currency is explicitly USD.

The authoritative executable shape check is `scripts/validate_input.py`. `scripts/calculate_or_transform.py`
contains the bounded calculation. The worked source fixture is `evals/files/request_example.json`;
it is explicitly synthetic and must not be used as current law or institutional policy.

No live preclearance integration, authenticated approval broker, system-of-record write, clearance issuance, notification, idempotent execution or rollback is implemented. Operational execution remains out of scope even with a supplied token. This does not place or execute trades.
