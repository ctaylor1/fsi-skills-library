# Adjacent-Skill Handoffs — market-risk-limit-monitor

This skill is a **scheduled, read-only, alert-only** monitor (risk tier R3). It produces a
cited limit-breach pack (`run_id`) with per-alert `fingerprint`s and stops. It does **not**
analyze root cause to disposition, recommend or construct remediating trades/hedges, change
or waive limits, or close breaches. Those are human risk-management and desk actions,
supported by the downstream skills below.

## Downstream (route the human reviewer to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `portfolio-exposure-analyzer` | Reviewer needs deeper factor / issuer / look-through exposure detail behind a VaR or concentration breach | `run_id` + unit + breached limit |
| `scenario-sensitivity-generator` | The sensitivity/scenario decomposition behind a stress-loss or Greek breach needs to be regenerated in detail | unit + `scenario_id` / sensitivity |
| `stress-test-scenario-designer` | A new or revised stress scenario is needed to probe the exposure behind a stress-loss breach | breached `scenario_id` + unit |
| `concentration-risk-monitor` | The exception is specifically a name/sector/curve concentration limit needing dedicated concentration monitoring | unit + concentration bucket |
| `liquidity-risk-scenario-analyzer` | A breach or proposed unwind raises a liquidity / liquidation-horizon question | unit + positions in question |
| `counterparty-exposure-monitor` | The exception concerns counterparty / settlement exposure rather than market-risk limits | unit + counterparty scope |
| `margin-collateral-optimizer` | The breach has margin / collateral implications the desk must work | unit + breached limit |
| `investment-committee-memo-builder` | A persistent or large breach must be escalated into a risk/investment-committee decision memo | `run_id` + breach evidence |
| `board-committee-pack-builder` | A breach must be packaged for a board / risk-committee pack | `run_id` + breach evidence |
| `regulatory-change-impact-analyzer` | A regulatory market-risk limit itself changed and the limit framework must be re-baselined | affected `limit_id`(s) + config version |

Remediation itself — hedging, cutting or rebalancing positions, granting or raising a limit
or temporary excess, waiving or closing a breach, or filing a breach/regulatory report — is
performed by the **market-risk manager, desk head, and risk committee** through their entitled
systems and governance process, never by this monitor. Where no catalog skill fits (for
example, actually executing a hedge, booking a limit change in the register, or transmitting a
regulatory breach notification), route to the appropriate **human risk-management, trading, or
regulatory-reporting function** — do not synthesize an action.

## Upstream (what invokes this skill)

This is a **scheduled monitor** (`aws-fsi-scheduled-agent: read-only-monitoring`): it is
triggered by its schedule (e.g., intraday and end-of-day risk runs), not by another skill. A
market-risk analyst or trading risk manager may also run it on demand against a specific book,
desk, or limit framework.

## Duplicate-execution prevention

- The monitor computes and evidences **breaches only**; it must not reach a disposition,
  instruct a desk, or take/recommend a trade, hedge, or limit change — those belong to the
  human reviewer and the downstream skills.
- Cross-run **deduplication** (fingerprint vs `open_alerts`) prevents the same persistent
  breach from being re-raised every scheduled run; still-open items remain visible as open
  rather than being silently cleared.
- Downstream skills consume the `run_id` / alert evidence rather than re-deriving limits or
  re-screening the whole book.
