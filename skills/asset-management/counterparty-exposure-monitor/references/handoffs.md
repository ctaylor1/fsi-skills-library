# Adjacent-Skill Handoffs — counterparty-exposure-monitor

This skill is a scheduled, read-only monitor. It produces a deduplicated, freshness-tagged
**alert set** (`run_id` + per-alert `fingerprint`) and enqueues it for a human. It does not
investigate to disposition, decide, or act. Downstream analysis and any action are the
reviewer's and the specialist skills' responsibility.

## Downstream (route the human/reviewer to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `portfolio-exposure-analyzer` | Reviewer wants an interactive breakdown of exposure composition / drivers behind an alert | `run_id` + alert `fingerprint`s |
| `liquidity-stress-analyzer` | A concentration/limit alert warrants scenario/funding-stress analysis | `run_id` + affected counterparties |
| `investment-committee-memo-builder` | The counterparty-risk picture must be packaged for IC review | alert set + evidence |
| `mandate-compliance-monitor` | The breach is actually a mandate/IPS limit question, not a counterparty credit limit | counterparty + limit context |

For **collateral/margin optimization**, **trade-break/settlement** disposition, or a
**counterparty credit decision**, there is no substitute for the desk and its controls:
route to the **counterparty-risk / treasury / collateral operations team** and the firm's
credit committee. Do not name a catalog skill that does not exist for those actions.

## Upstream (may schedule / consume this monitor)

Runs on a schedule; it may also be invoked ad hoc by a **counterparty-risk or treasury
reviewer**. Its alert set can feed the human queue that `investment-committee-memo-builder`
or `portfolio-exposure-analyzer` draws on. No skill uses this monitor to take an action.

## Sibling monitors (distinct scope — do not duplicate)

- `mandate-compliance-monitor` — investment mandate / IPS guideline limits (not counterparty
  credit/settlement exposure).
- `investment-thesis-monitor` — research/thesis triggers, not exposure limits.
- `market-risk-limit-monitor` (Risk Management) — market-risk (VaR/greeks) limits.
- `concentration-risk-monitor` (Risk Management) — firm-wide concentration across risk types.
- `post-trade-settlement-monitor` (Capital Markets) — settlement-fail monitoring, not
  aggregate counterparty exposure vs limits.

If the request is really one of the above, route there rather than re-scoping this monitor.

## Duplicate-execution prevention

- This monitor **only** aggregates, thresholds, dedups, tags freshness, and queues. It must
  not investigate to disposition, contact a counterparty, or take/recommend an action.
- Alerts carry a stable `fingerprint`; a re-run marks an already-open issue `recurring`
  rather than raising a duplicate. Downstream skills consume the `run_id`/`fingerprint`
  evidence instead of recomputing exposures.
