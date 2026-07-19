---
name: portfolio-rebalancing-assistant
description: >-
  Assess a portfolio's drift from its target model and the tax, liquidity, restriction, and
  cost impacts of correcting it, then prepare a validated, idempotent proposed trade list
  (buys/sells) and stage it for advisor and client authorization before any order is routed.
  Use when an advisor, portfolio manager, or trading associate needs to rebalance an account
  end to end with a controlled plan → validate → authorize → execute → verify → audit
  workflow, or to execute an already-authorized rebalance plan and verify the fills. This
  skill produces proposed trades and, only AFTER a valid advisor AND client authorization
  token bound to the plan, executes them idempotently with verification and rollback. HARD
  BOUNDARY: it never routes, submits, or executes any order, and never changes a holding or
  system of record, without that two-party authorization; it never gives personalized
  investment or tax advice; and it fails closed on anything over limit, restricted,
  irreversible, or out of policy.
license: MIT
compatibility: Amazon Quick Desktop; requires CRM, portfolio-accounting/OMS-EMS, planning-engine (IPS/target model), product-and-market-data, restrictions/mandate, approved-tax-assumptions, and permission/approval-broker MCP integrations. Read-only for planning; the execute operation is approval-gated (advisor + client) and idempotent.
metadata:
  aws-fsi-category: "Wealth Management"
  aws-fsi-skill-type: "Workflow or orchestration skills"
  aws-fsi-risk-tier: "R4"
  aws-fsi-archetype: "Orchestrate & resolve"
  aws-fsi-agent-pattern: "Plan-validate-execute workflow agent"
  aws-fsi-delivery-wave: "Wave 4 - gated orchestration"
  aws-fsi-action-mode: "Approval-gated write or submission"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Wealth Management advisory & compliance"
  aws-fsi-primary-user: "Advisor / portfolio manager / trading associate"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Portfolio Rebalancing Assistant

## Purpose and outcome
Rebalance an account through a controlled workflow: measure **drift** from the target model,
quantify the **tax, liquidity, restriction, and cost** impacts of correcting it, build a
**validated trade plan** (idempotent buy/sell steps, preconditions, expected post-state,
verification, rollback), and — **only after advisor AND client authorization** — route the
orders and verify the fills, leaving a complete audit trail. The outcome is a rebalanced
portfolio at its target weights with evidence that every trade was authorized, verified, and
reversible — or a documented proposed trade list awaiting authorization.

## Use when
- "Rebalance this account back to its model and stage the trades for approval."
- "Build the proposed trade list for account X, with the tax and cost impact."
- "Execute the authorized rebalance plan and confirm the fills posted."

## Do not use
- **Drift / exposure analysis only** with no rebalance intent → use
  `portfolio-exposure-analyzer`, `portfolio-holdings-summarizer`, or
  `portfolio-risk-diversification-check`.
- **The investment recommendation or suitability decision** ("should this client rebalance?",
  best-interest sign-off) → the licensed advisor and `suitability-reg-bi-reviewer`.
- **Personalized tax strategy** (specific-lot harvesting beyond the approved assumption set) →
  a licensed tax advisor.
- **Comparing target proposals** → `portfolio-proposal-comparator`; **income/withdrawal
  modeling** → `retirement-income-scenario-modeler`.
- Any trade **not permissible**, over the authority limit, restricted, irreversible, or
  requiring a policy exception → stop and escalate to a human authority; do not improvise.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Upstream analysis and IPS skills may
hand a target model and drift context here; this skill owns the plan → execute lifecycle and
emits a `plan_id` + audit record. It never duplicates drift-analysis, suitability, or
tax-advice work, and only this skill submits the orders.

## Inputs and prerequisites
- A rebalance request: `account_id`, `account_type` (discretionary / non-discretionary),
  `model_id`, target weights, current `portfolio` (holdings, cost basis, tax lots, cash),
  `restrictions`, `limits`, and `proposed_actions`. Schema:
  [scripts/validate_input.py](scripts/validate_input.py) and
  [references/domain-rules.md](references/domain-rules.md).
- The versioned **target model / IPS**, **restrictions/mandate** list, and **approved
  tax-assumption** set.
- Read access for planning; the approval-gated **execute** operation and **both** an advisor
  and a client authorizer. See [references/controls.md](references/controls.md).

## Source hierarchy
See [references/source-map.md](references/source-map.md). Portfolio accounting/OMS is the
system of record for holdings, cash, and post-trade verification; the planning engine
supplies the target and drift bands; the restrictions and tax-assumption services are
versioned contracts. The plan never invents a target the model did not supply.

## Workflow (plan → validate → authorize → execute → verify → audit)
1. **Measure drift** — read current holdings and the target model; identify the asset-class
   sleeves that breach the drift band. Run `validate_input`.
2. **Assess impacts** — for the proposed trades, estimate realized gain/loss (short-term vs.
   long-term), wash-sale risk, funding/settlement, turnover, concentration, and cost. Any
   breach → fail closed and escalate.
3. **Plan (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to build the trade
   plan: ordered buy/sell steps each with an **idempotency key**, precondition, expected
   effect, **verification**, and **rollback**; plus the expected post-state (weights vs.
   target), a compliance summary, and the plan hash. The plan starts advisor + client
   `pending`, execution `blocked`.
4. **Validate the plan** — run [scripts/validate_output.py](scripts/validate_output.py):
   actions permissible/in-limit, every step idempotent + verifiable + reversible, compliance
   clean, amounts tie, and execution blocked pending both authorizations. Fail closed on any
   miss.
5. **Authorize** — present the proposed trades for **advisor** authorization and, for a
   non-discretionary account, **client** authorization. Each authorization supplies a token
   bound to the plan hash. Without the required token(s) — the advisor token always, plus the
   client token for a non-discretionary account — no execution.
6. **Execute** — only with both valid tokens: route each order **idempotently**
   (re-submitting a filled step with the same key must not double-trade). Stop on the first
   failed precondition/verification.
7. **Verify** — confirm the actual post-state (fills + resulting weights) equals the expected
   post-state; if not, invoke **rollback** and report.
8. **Audit** — record plan, both approvers, tokens, each fill, verification, and any rollback.

## Validation loop
`validate_input` before planning; `validate_output` after planning **and** again before
execution (re-check the plan is still blocked/pending and unchanged). After execution, verify
post-state; on mismatch, roll back and fail closed. Never assume automatic retries.

## Human approval
`required` — **mandatory before any order is routed or submitted**. Authorization is
**two-party**: a licensed **advisor** token and a **client** token (a discretionary account
still requires the advisor token; a non-discretionary account additionally requires the
client token). Each token binds to the exact plan hash, so an altered plan voids both.
Over-limit, restricted, or irreversible trades are out of scope for auto-planning and require
a higher authority.

## Failure handling
- **Trade not permissible / over limit / restricted / irreversible / wash sale / underfunded /
  over turnover** → fail closed; escalate; no plan executes.
- **Precondition fails at execute** (holding moved, cash short, symbol newly restricted) →
  stop; do not force; report the blocking state.
- **Verification mismatch after a fill** → **roll back** and halt; report.
- **Partial fills / tool timeout** → leave the account consistent (rolled back to last
  verified checkpoint); never leave a half-rebalanced book; no silent retry.
- **Altered plan / stale token** → refuse to execute; re-plan and re-authorize.

## Output contract
1. **Proposed trade plan** — `plan_id`, account, model, ordered steps (idempotency key,
   precondition, expected effect, verification, rollback), expected post-state, compliance
   summary (tax, turnover, cost, drift), `plan_hash`, advisor + client `pending`, execution
   `blocked`.
2. **Validation result** — plan checks passed/failed.
3. **Execution record** (post-authorization) — both tokens, per-step fill, verification,
   rollback if any.
4. **Audit trail** — actors, both approvers, timestamps, before/after weights, versions used.
5. **Standing note** — "Proposed trades only; no order has been routed or submitted... "
   (before execution).
See [references/controls.md](references/controls.md).

## Privacy and records
Customer NPI/PII. Mask account identifiers to last 4 in presentation. Retain plan,
authorizations, execution, verification, and rollback records per books-and-records
requirements; the audit trail is immutable and complete, and logs both approvers, the actor,
and the policy/model/tax-assumption versions used.

## Gotchas
- **Two tokens, not one.** A non-discretionary account needs both advisor and client
  authorization; a single approval is not enough to trade.
- **Authorization binds to the plan, not the account.** Editing the trade list after
  authorization voids both tokens — re-authorize.
- **Idempotency is mandatory.** A re-submitted order must be a no-op if already filled; use
  the idempotency key, never assume "it probably didn't route."
- **Reversibility first.** A trade that cannot be cancelled or offset needs a higher control
  and is out of scope for auto-planning.
- **Verify against fills, not the plan.** Post-trade verification reads the OMS/portfolio
  system; do not "confirm" from the plan you just wrote.
- **Estimates, not advice.** Realized-gain and cost figures are planning estimates under the
  approved tax-assumption version — never personalized tax or investment advice.
- **Only rebalance what drifted.** Do not widen the plan beyond the sleeves that breach the
  band or the symbols/amounts the request authorized.
