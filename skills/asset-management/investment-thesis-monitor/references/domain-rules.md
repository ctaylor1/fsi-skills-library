# Domain Rules — investment-thesis-monitor

Explainable thesis **signals**, how freshness gates them, and how the fired set maps to an
**escalation band** and a deduplicated review queue. Tolerances are configuration (versioned,
owned by the research/investment platform team), not hard-coded judgments, and are never
tuned to force a particular alert. The firm's investment-process and research-supervision
standards take precedence.

## Signal taxonomy

Each signal is tagged **confirming** (thesis playing out) or **challenging** (thesis at risk).
A signal only fires on **fresh** evidence (observed within `max_staleness_days`); stale
evidence is reported `not_evaluable`.

| Signal | Side | Fires when (default config) | Evidence attached |
| ------ | ---- | --------------------------- | ----------------- |
| `kpi_miss` | challenging | A tracked KPI is below expectation by ≥ `kpi_tolerance` (default 15%, direction-aware) | KPI name, expected, actual, relative delta |
| `kpi_beat` | confirming | A tracked KPI is above expectation by ≥ `kpi_tolerance`, with no miss | KPI name, expected, actual, relative delta |
| `catalyst_missed` | challenging | A documented catalyst has status `missed`, or is `pending` past its `due_by` | Catalyst name, status, due date |
| `catalyst_met` | confirming | A documented catalyst has status `met` | Catalyst name |
| `estimate_revision_down` | long→challenging / short→confirming | Consensus EPS revised down by ≥ `estimate_revision_pct` (default 10%) | Prior vs current consensus, revision % |
| `estimate_revision_up` | long→confirming / short→challenging | Consensus EPS revised up by ≥ `estimate_revision_pct` | Prior vs current consensus, revision % |
| `stop_breach` | challenging | Price crossed the thesis stop against the position (long: ≤ stop; short: ≥ stop) | Price + stop + price date |
| `price_target_breach` | confirming | Price reached the thesis target in the position's direction | Price + target + price date |
| `risk_news` | challenging | A monitored thesis risk appears in news/filings within `lookback_days` | Risk tag + source |

Signals are **additive, independent, and explainable** — there is no opaque composite
"thesis score". The output reports each signal that fired with its own cited evidence, plus
the confirming/challenging **stance** of the thesis this run (`confirming`, `challenging`,
`mixed`, or `none`).

## Escalation mapping (deterministic, documented)

Driven only by the **challenging** signals that fired. Escalator set = `{stop_breach,
catalyst_missed}`.

| Suggested band | Rule |
| -------------- | ---- |
| **Elevated** | ≥ 3 challenging signals fired, OR any escalator (`stop_breach` / `catalyst_missed`) fired |
| **Review** | 1–2 challenging signals fired, no escalator |
| **Informational** | No challenging signal fired but ≥ 1 confirming signal (thesis on-track / milestone) |
| _(no alert)_ | No signal fired on fresh evidence |

The band is a **triage suggestion for the covering analyst and PM**. It is not a
buy/sell/hold decision, a thesis close/retire, or investment advice, and it never triggers a
trade or rebalance.

## Freshness handling

- Age each evidence row (`observed_at` / `price_asof`) against the run `as_of`.
- Evidence older than `max_staleness_days` (default 21) is `not_evaluable`; its signal does
  **not** fire. A monitor never guesses on stale data.
- A thesis with **zero** fresh evidence this run is a `freshness_gaps` item (feed to refresh),
  not a breach.

## Deduplication & escalation latency

- Each alert carries `alert_key = thesis_id`. If an **open** alert with the same key exists in
  `prior_alerts`, the new alert is a **continuation**: `duplicate = true`, routed to
  `queue.deduplicated`, and **not re-raised as a new escalation**. This prevents alert storms
  and keeps escalation latency measured from the first raise, not every run.
- New (non-duplicate) alerts route to `queue.new`. `queue.by_escalation` groups every alert
  key under its band for the analyst queue.

## Hard boundaries (fail closed)

- Never state or imply a **buy/sell/hold/trim/add/exit** decision, a **thesis close/retire**,
  a **rebalance**, or a **trade/order** — those are human PM/analyst actions.
- Never give **personalized investment advice** ("you should buy/sell").
- Never **tune tolerances** to force or suppress an alert for a given name; use only the
  versioned config.
- Never fire a signal on **stale** evidence, and never present a band as a decision.
