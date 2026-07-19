# Source Map — portfolio-rebalancing-assistant

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Portfolio accounting / OMS-EMS** (system of record) | Current holdings, cost basis, tax lots, cash, preconditions, and post-trade fill/position verification | Read for planning; **approval-gated write** to route/submit orders on execute |
| 2 | **Planning engine / IPS + target model** (versioned) | Target allocation, drift bands, rebalance policy | Read-only |
| 3 | **Restrictions & mandate service** | Client/legal restrictions, do-not-buy list, concentration and mandate limits | Read-only |
| 4 | Approved **tax-assumption set** (versioned) | Realized gain/loss estimates, short-term budget, wash-sale window | Read-only |
| 5 | **Product & market data** | Prices, security master, asset-class mapping, transaction-cost proxies | Read-only |
| 6 | **CRM** | Account type (discretionary vs. non-discretionary), authorization contacts | Read-only |
| 7 | **Permission / approval broker** | Advisor + client authorization tokens, role checks, execute gating, audit | Controlled |

The planning engine, restrictions/mandate service, and tax-assumption set are **versioned
contracts**; the plan records the versions it relied on. Where sources conflict, the system
of record (portfolio accounting) governs current state and the planning engine governs the
target — the plan never invents a target the model did not supply.

## Least-privilege operations (deployment)

Separate, single-purpose operations (never a combined "rebalance it"):

- `portfolio.read(account_id)` / `positions.read` / `taxlots.read` — read-only.
- `model.read(model_id)` → target weights + drift bands — read-only, versioned.
- `restrictions.read(account_id)` → restricted symbols / mandate limits — read-only.
- `tax.estimate(lots, actions)` → realized gain/loss + wash-sale flags — read-only, deterministic.
- `approval.request(plan_hash, party)` → advisor token, then client token (human-in-the-loop).
- `oms.submit(order, idempotency_key, advisor_token, client_token)` — **approval-gated,
  idempotent write**; rejects a missing/invalid token pair or a stale plan hash.
- `oms.verify(account_id, expected_post_state)` — read-only post-trade check of fills/weights.
- `oms.cancel_or_reverse(order, idempotency_key, token)` — cancel an unfilled order or route
  an offsetting trade (rollback).
- `audit.record(plan_id, events)` — append-only audit.

Each operation stays below the fixed timeout; multi-order execution is a **resumable staged**
process keyed by `plan_id` + step idempotency keys. No hidden retries; no step-up assumed.

## Citation / identifier format

`portfolio:{acct=****NNNN};{symbol}@{state-read-time}` and
`model:{model_id}@{policy_version}`. The plan records the exact pre-state reads (positions,
cash, tax lots, restrictions) it relied on so verification and audit are reproducible.
