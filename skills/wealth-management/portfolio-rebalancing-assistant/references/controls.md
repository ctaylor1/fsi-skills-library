# Controls — portfolio-rebalancing-assistant

- **Risk tier:** R4 — approval-gated action. **Action mode:** Approval-gated write or submission.
- **Human approval:** `required` — mandatory before **any** order is routed or submitted.
  Authorization is **two-party**: a licensed **advisor** token **and** a **client**
  authorization token, each bound to the plan hash. No token pair, no execution.

## Prohibited (fail closed)

- **Execution without a valid advisor AND client token** matching the plan hash and limits.
- **Personalized investment or tax advice.** This skill prepares and validates a proposed
  trade list; it does not recommend that a client should rebalance, nor opine on tax
  strategy. Suitability and advice are the licensed advisor's judgment.
- Any action **outside the permissible set** (only `buy` / `sell` to reach the model target),
  **over the per-order authority limit**, or that is **not reversible** (cannot be cancelled
  or offset).
- **Buying a restricted security**, breaching the **concentration cap**, exceeding the
  **short-term realized-gain budget**, exceeding the **turnover ceiling**, a **wash-sale**
  repurchase, or an **underfunded** (non-settling) plan.
- **Widening the plan** beyond the sleeves that breach the drift band, or beyond the symbols
  and amounts the request authorized.
- **Continuing past a verification mismatch** or a failed precondition; **silent retries**;
  or assuming step-up authorization.

## Segregation of duties

The skill that plans is **not** an approving party. The advisor who authorizes and the
client who authorizes are distinct from the automated planner, and from each other. A
discretionary account still requires the advisor token; a **non-discretionary** account
additionally requires the **client** token before any submission.

## Required plan/output screens (`scripts/validate_output.py`)

- Every action is a permissible trade within the per-order authority limit.
- Every step has: idempotency key, precondition, expected effect, verification, rollback.
- Compliance is clean: no restricted buys, no wash-sale, short-term gain within budget,
  turnover within ceiling, post-trade drift within tolerance.
- Turnover is at or under the ceiling the plan recorded (sourced from the versioned policy
  contract, tightened by the request — never a value hardcoded in the validator).
- Amounts tie: net cash after trades reconciles to the expected post-state cash.
- `plan_hash` is **present** and matches the plan contents; a missing or blank hash **fails
  closed** (tamper detection cannot be bypassed by dropping the field).
- Pre-execution: execution is `blocked` and **both** advisor and client approvals are
  `pending`; the standing note is present.
- No step is marked executed without a valid **advisor** token (always required); a
  **non-discretionary** account additionally requires a valid **client** token, while a
  **discretionary** account executes on the advisor token alone. A missing/unknown
  `account_type` is treated as non-discretionary (client token still required). Otherwise
  **fail closed**.

## Idempotency, verification, rollback

- Idempotency key is deterministic from `{plan_id, step_id, action, symbol, amount}`;
  re-submitting a step with the same key is a no-op if the order already filled.
- Verification reads the **OMS/portfolio system** (fills and resulting weights), never the
  plan, and must match the expected post-state.
- Rollback cancels an unfilled order or routes an offsetting trade back to the last verified
  checkpoint; a partially filled plan is never left drifting.

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII).** Mask account identifiers to last 4.
- Immutable, complete **audit trail**: plan, hash, advisor + client approvers and tokens,
  per-step fill result, verification, rollback, actor identities, timestamps, and the policy /
  model / tax-assumption versions used. Retain per books-and-records requirements.
