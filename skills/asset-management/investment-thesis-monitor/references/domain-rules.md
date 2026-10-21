# Domain Rules — investment-thesis-monitor

## Supplied-input validation boundary

The bundled scripts operate on supplied JSON. Connector access, source extraction, authenticated approvals and external delivery are not implemented by these scripts. Retain the original input separately and run `python -B scripts/validate_output.py output.json --input input.json` (alias `--source`). Output includes `input_hash` and `source_truth: unverified`; validation reconstructs the native result and rejects changed figures, narrative, classifications, omitted fields and extra fields. A successful check proves correspondence with the supplied input, not source truth, legal applicability or permission to distribute. Never add a raw source snapshot to an outward-facing artifact. Source and approval strings remain supplied evidence for professional review.

Future and unparseable observations never fire. Zero prior EPS produces a not-evaluable percentage revision. Deduplication requires an open thesis alert with the same evidence_fingerprint and escalation; new or changed evidence is re-raised. monitor_run_id binds the complete supplied snapshot. This is an offline calculation, not a scheduled live feed.


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

- Each alert carries `alert_key = thesis_id` and an `evidence_fingerprint`. Only an open prior alert with the same fingerprint and escalation is a duplicate. A legacy prior key without an evidence fingerprint, changed evidence, or a changed escalation is a new alert.
- New (non-duplicate) alerts route to `queue.new`. `queue.by_escalation` groups every alert
  key under its band for the analyst queue.

## Hard boundaries (fail closed)

- Never state or imply a **buy/sell/hold/trim/add/exit** decision, a **thesis close/retire**,
  a **rebalance**, or a **trade/order** — those are human PM/analyst actions.
- Never give **personalized investment advice** ("you should buy/sell").
- Never **tune tolerances** to force or suppress an alert for a given name; use only the
  versioned config.
- Never fire a signal on **stale** evidence, and never present a band as a decision.
