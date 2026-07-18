# Adjacent-Skill Handoffs — investment-thesis-monitor

This skill runs on a schedule, produces a cited **alert queue** (`monitor_run_id`, per-alert
`alert_key`), and stops. It does not analyze to a disposition, model, draft, decide, or act.
Downstream analysis/drafting skills — and the covering analyst/PM — consume the alerts.

## Downstream (route the analyst/PM to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `earnings-results-analyzer` | An Elevated alert is driven by an earnings/KPI print that needs a full read-through of results and guidance | `alert_key` + fired KPI/estimate evidence |
| `scenario-sensitivity-generator` | Consensus estimates moved and the thesis needs re-testing under revised drivers | `alert_key` + estimate-revision evidence |
| `dcf-modeler` | The valuation case needs rebuilding after a target/stop breach or estimate cut | security + revised drivers |
| `coverage-initiation-researcher` | The thesis is materially broken and warrants fresh, deep re-research | `alert_key` + challenging evidence |
| `performance-attribution-builder` | The PM wants the position's contribution attributed for a review | position + period |
| `investment-committee-memo-builder` | A materially challenged thesis needs an IC memo for a position review/decision | `alert_key` + evidence bundle |
| `fund-commentary-drafter` | Confirming or challenging evidence needs write-up for periodic fund commentary | `alert_key` + stance + evidence |

## Sibling monitors (do not duplicate — route by scope)

| Sibling skill | Owns |
| ------------- | ---- |
| `mandate-compliance-monitor` | Fund mandate / investment-guideline limit monitoring (not thesis KPIs) |
| `counterparty-exposure-monitor` | Counterparty exposure limits (not single-name thesis health) |

If the request is really about a guideline/mandate limit or counterparty exposure, route to
the sibling monitor rather than stretching a thesis signal to cover it.

## Upstream (may invoke this monitor)

A **scheduled runner** (read-only monitoring) invokes this skill on a cadence over the active
thesis book. There is no human "case" upstream; the monitor's output is the input to human
review and to the downstream analysis/drafting skills above.

## Human / specialist handoffs (no catalog skill applies)

- **Any trade, rebalance, trim/add, exit, or hedge** → the covering **PM / trading desk**.
  The monitor never stages or recommends these.
- **A decision to close or retire a thesis** → the **research supervisor / PM**, per the
  investment process.
- **Personalized investment advice** → a **licensed investment professional**; out of scope
  for this monitor.

## Duplicate-execution prevention

- This monitor computes and evidences **signals and an escalation band only**; it must not
  reach a buy/sell/hold decision, model, draft, close the thesis, or act.
- Alerts carry a durable `alert_key`; open alerts are **deduplicated** across runs so a
  continuation is not re-raised. Downstream skills reuse the `alert_key` evidence rather than
  re-deriving it.
