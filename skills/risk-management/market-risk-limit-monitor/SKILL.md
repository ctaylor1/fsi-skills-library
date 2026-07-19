---
name: market-risk-limit-monitor
description: >-
  Scheduled, read-only market-risk monitor that tests trading books and desks against
  versioned VaR, expected-shortfall, sensitivity (DV01/CS01/vega), stress-loss, notional, and
  concentration limits; classifies each utilization PASS/WARN/BREACH with cited evidence, flags
  current vs pre-deal (projected) breaches, deduplicates against open breaches, checks
  measurement freshness, and queues severity-ranked alerts to human market-risk reviewers. Use
  when a scheduled run (or a market-risk analyst / trading risk manager) needs to surface limit
  breaches, near-limit warnings, stress-loss exceedances, or pre-deal limit hits with
  source-linked evidence for escalation. HARD BOUNDARY: ALERTS ONLY — never trades, hedges,
  cuts, or rebalances a position; never grants, raises, or waives a limit or excess; never
  clears or closes a breach; never closes or downgrades an alert; never files a breach or
  regulatory report; never writes to any book of record. Every disposition and remediation is a
  human risk-management decision.
license: MIT
compatibility: Amazon Quick Desktop; requires read-only market-risk-engine (VaR/ES/sensitivities/stress P&L), position/sub-ledger, limit & risk-appetite register, scenario library, market & reference data, and prior-breach register MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Risk Management"
  aws-fsi-skill-type: "System-interaction or operational skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Monitor & alert"
  aws-fsi-agent-pattern: "Scheduled monitor + human queue"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Scheduled read-only; alert only"
  aws-fsi-scheduled-agent: "read-only-monitoring"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Confidential"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Enterprise Risk Management"
  aws-fsi-primary-user: "Market-risk analyst / trading risk manager"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Market Risk Limit Monitor

## Purpose and outcome
Given a set of trading **books / desks / firm units**, their **measured risk numbers** (VaR,
expected shortfall, sensitivities, stress P&L, notional, concentration), and a **versioned
limit register**, evaluate every unit against every configured limit; classify each result
**PASS / WARN / BREACH** against the limit; attach cited evidence; distinguish **current**
breaches from **pre-deal (projected)** breaches; deduplicate against already-open breaches;
flag stale measures; and emit **severity-ranked alerts** to human market-risk queues. A
successful run lets a market-risk analyst or trading risk manager see, with evidence, exactly
which limits are breached (or approaching), which pending trades would newly breach, and what
is new since the last run — so a **human** can adjudicate and remediate. This is a
**scheduled, read-only, alert-only** monitor (risk tier R3): it packages exceptions with
mandatory human adjudication; it does not resolve them.

## Use when
- A scheduled intraday / end-of-day risk run needs to screen limits for breaches and
  near-breaches.
- "Which books are over their VaR, ES, or stress-loss limits right now?"
- "Would this pending trade push the desk DV01 (or VaR) over its limit before we work it?"
  (pre-deal check)
- "Are any desks breaching the 2008-crisis stress-loss limit, with evidence to escalate?"
- A reviewer wants a consistent, cited breach queue with new-vs-still-open separation.

## Do not use
- The user wants the monitor to **fix** a breach — put on a hedge, cut/rebalance a position,
  or grant a limit excess/waiver → out of scope; this monitor alerts only. Route the human to
  the desk / risk manager and their entitled systems (and, for analysis, to the downstream
  skills in [references/handoffs.md](references/handoffs.md)).
- **Deeper exposure / factor / look-through** analysis behind a breach →
  `portfolio-exposure-analyzer`. **Sensitivity / scenario decomposition** →
  `scenario-sensitivity-generator`. **New stress-scenario design** →
  `stress-test-scenario-designer`.
- **Liquidity / liquidation-horizon** questions → `liquidity-risk-scenario-analyzer`.
  **Counterparty / settlement** exposure → `counterparty-exposure-monitor`.
- The **limit itself changed** (regulation / risk-appetite update) and the register must be
  re-baselined → `regulatory-change-impact-analyzer`.
- Personalized **investment / trading advice** (what to trade or hedge) → out of scope; not
  licensed advice.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a cited breach pack
with a durable `run_id` and per-alert `fingerprint`s; downstream analysis, scenario, and
escalation skills consume it. It must not duplicate their disposition or remediation steps,
and it never closes a breach or changes a limit itself.

## Inputs and prerequisites
- One or more **units** with `unit_id`, `unit_type` (book/desk/firm), `desk`,
  `measured_as_of`, and `measures` (each with `metric`, `value`, `unit`, and the metric
  discriminators: `horizon`+`confidence` for VaR/ES, `sensitivity` for Greeks, `scenario_id`
  for stress, `sub_scope` for concentration; optional `projected_value` for pre-deal checks).
- The **versioned limit set** (`config_version`): `limit_id`, `metric`, `scope`+`scope_value`,
  `direction` (max/min), `limit_value`, and `warn_buffer_pct`.
- `max_staleness_hours` for freshness, and the **prior open-breach** fingerprints for
  deduplication. Schema and validation: [scripts/validate_input.py](scripts/validate_input.py).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The **limit register is the
definition of record** for every limit; the **risk engine is the book of record for the risk
numbers** (this monitor reads VaR/ES/stress — it never re-derives or aggregates them). Cite
every alert's evidence to a measured row and the limit to its `config_version`. Never infer a
limit from the exposure or an assertion.

## Workflow
1. **Load & validate** — pull the versioned limits, measured risk numbers, pending pre-deal
   exposure, and prior open breaches for the run; validate with `validate_input`.
2. **Check freshness** — compute `staleness_hours` per unit; mark any exceeding
   `max_staleness_hours` as stale and raise a freshness alert. Never drop or silently refresh.
3. **Evaluate limits (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to join each limit
   to its unit's matching measure and classify PASS/WARN/BREACH, computing both **current**
   breaches and **pre-deal (projected)** breaches. Each alert carries measured value,
   utilization %, limit, and cited evidence.
4. **Score & route** — map each alert to a deterministic `severity` and routing `queue` per
   the documented mapping ([references/domain-rules.md](references/domain-rules.md)). This is
   a triage suggestion for a human, not a risk determination.
5. **Deduplicate** — fingerprint each alert and split **new** vs **still-open** against the
   prior open-breach baseline so persistent breaches do not re-alert every run.
6. **Package the queue** — emit the alert pack (summary, per-alert evidence, escalations with
   SLA, freshness, disclaimer) to the market-risk queues for human adjudication.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check confirms: every alert is well-formed with cited evidence; severity and
queue tie out deterministically; deduplication partitions new vs still-open; stale units are
flagged (never suppressed); **no autonomous-action / decision / closure / filing language** is
present; the standing disclaimer is present; and escalation counts tie out. Fail closed on any
miss.

## Human approval
`required` (R3): human risk-management adjudication is mandatory before any regulated
decision, disposition, limit change, waiver, breach/regulatory filing, external delivery, or
write to a case/system of record. The scheduled read and the internal queue are the monitor's
only outputs. **Every disposition — hedge, trade, limit change, waiver, breach closure, or
filing — is a human action**; the monitor never performs or recommends one.

## Failure handling
- **Stale measures** (older than `max_staleness_hours`) → flag the unit, mark its alerts
  `stale_input`, treat results as low-confidence; do not present as current.
- **Missing / ambiguous limit** → report the gap; never invent or guess a threshold.
- **No matching measure** for a limit (unit or metric absent) → the limit is not evaluable;
  surface it via input warnings rather than assuming PASS.
- **Register vs. risk-engine conflict** (e.g., which unit a limit applies to) → cite both; do
  not resolve silently.
- **No prior open-breach baseline** → deduplication is disabled; report everything as new and
  say so. **Tool timeout** → return alerts computed so far with an "incomplete" flag; assume
  no automatic retry.

## Output contract
1. **Summary** — run id, as-of, units/limits evaluated, counts (new, deduplicated, warn,
   breach), and stale units.
2. **Alerts** — per alert: unit, desk, limit, metric/bucket, status, breach_type
   (current/projected/freshness), measured vs limit, utilization %, severity, routing queue,
   cited evidence, and `is_duplicate` / `stale_input` flags.
3. **Escalations** — severity buckets with counts, target queues, and indicative SLA.
4. **Data freshness** — per unit staleness (hours) and stale flag.
5. **Machine-readable** — alerts + `new_alerts` / `still_open` fingerprints + `run_id`.
6. **Standing disclaimer** — "Monitoring alert only; no trade, hedge, position change, limit
   change, waiver, breach closure, or system-of-record change has been made. Market-risk limit
   exceptions require human risk-management review and disposition."
See [references/controls.md](references/controls.md).

## Privacy and records
Positions, risk numbers, and limit utilization are **Confidential** and commercially
sensitive. Minimize data in the pack to what evidences an alert. Retain each run's alerts +
citations + `config_version` per records policy; log the read, the queue emission, and any
required human adjudication / external-delivery approval. Route alerts only to approved
market-risk queues; never exfiltrate positions or risk numbers.

## Gotchas
- **An alert is not a decision or an action.** A BREACH justifies *review and adjudication*,
  never a monitor-initiated hedge, trade, limit change, waiver, or breach closure.
- **Current vs. pre-deal breaches.** A `current` breach is the measured utilization now; a
  `projected` breach is a pending trade that would *newly* breach — the active pre-deal signal
  worth catching before the order is worked. Both are alerts, not blocks.
- **Read risk numbers; do not re-derive them.** VaR/ES/stress come from the risk engine and
  are not additive across books — a desk/firm limit needs a pre-aggregated unit, never a sum
  of book VaR.
- **Deduplicate, don't silence.** Still-open breaches must remain visible as open; the
  fingerprint logic prevents re-alerting, not tracking.
- **Stale data is dangerous.** A "clean" run over hours-old measures can hide a live breach —
  always surface staleness rather than presenting stale results as current.
- **Limits are versioned config, not judgement.** Never tune a threshold to a desk or infer
  "what's acceptable here"; cite the limit and its `config_version`.
- **Boundary buckets.** Utilization exactly at 100% (measured = limit) is WARN, not BREACH —
  the engine breaches only when strictly over (or under, for floors).
