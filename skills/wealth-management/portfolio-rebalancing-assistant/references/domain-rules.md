# Domain Rules — portfolio-rebalancing-assistant

The firm's rebalance policy, the account's **IPS / target model** (versioned), the
**restrictions/mandate** service, and the **approved tax-assumption set** (versioned) govern.
Nothing outside these may be planned or executed by this skill.

## Permissible actions and limits (default policy)

| Rule | Default | Enforced by |
| ---- | ------- | ----------- |
| Permissible actions | `buy`, `sell` only (to reach the model target) | `validate_input`, `validate_output` |
| Per-order authority limit (`max_order_notional`) | ≤ 250,000 notional | both scripts |
| Plan turnover ceiling (`max_plan_turnover_pct`) | sell notional ÷ total value ≤ 30% | `validate_input`, plan builder |
| Short-term realized-gain budget (`st_gain_budget`) | ≤ 10,000 realized short-term gain | `validate_input`, plan builder |
| Concentration cap (`max_position_weight_bps`) | post-trade single position ≤ 4,500 bps | `validate_input` |
| Drift band (`drift_tolerance_bps`) | rebalance only sleeves outside ±500 bps of target | `validate_input`, plan builder |

The request may **tighten** these via a `limits` block; the plan records the effective
limits used. Requests that breach any limit, buy a restricted security, trigger a wash sale,
or cannot settle are **out of scope** — the builder returns a REJECTED plan and escalates.

## Tax, wash-sale, and funding rules

- **Realized gain/loss** is estimated proportionally per lot under the approved
  tax-assumption version; short-term (`holding_days < 365`) realized gains count against the
  budget. Long-term gains are reported, not budget-gated.
- **Wash sale:** selling a symbol at a loss and (re)buying the same symbol in the same plan
  is disallowed (substantially-identical, 30-day rule). Fail closed.
- **Funding / settlement:** buys must be fundable by available cash plus sell proceeds; an
  underfunded plan cannot settle and is rejected.
- These are estimates for planning only — **not** personalized tax advice.

## Plan requirements (every step)

- **Idempotency key** deterministic from `{plan_id, step_id, action, symbol, amount}`;
  re-submitting a filled step is a no-op.
- **Precondition** read from the OMS/portfolio system at execute time (holding held to sell;
  settled cash to buy; symbol not restricted) — checked, not assumed.
- **Expected effect** with a notional that ties to the target weight movement.
- **Verification** that reads fills and resulting weights after the trade and compares to
  the expected post-state.
- **Rollback** that cancels an unfilled order or routes an offsetting trade to the last
  verified checkpoint.

## Two-party approval binding

- Authorization yields **two tokens** — one from the licensed **advisor**, one from the
  **client** — each bound to the **plan hash**.
- A **discretionary** account requires the advisor token; a **non-discretionary** account
  additionally requires the client token before any submission.
- Any change to the plan after authorization changes the hash and **voids** both tokens.
- Execution is permitted **only** with the valid token pair whose amounts remain within the
  authority limits.

## Post-state verification & rollback

- Verify the **actual** post-state (read fills and weights) equals the expected post-state,
  with every traded sleeve inside the drift band. On mismatch, **roll back** and halt.
- On partial completion, roll back to the last verified checkpoint so the account is never
  left half-rebalanced.
