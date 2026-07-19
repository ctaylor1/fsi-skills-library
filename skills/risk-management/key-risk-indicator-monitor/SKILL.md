---
name: key-risk-indicator-monitor
description: >-
  Scheduled, read-only monitor that evaluates enterprise Key Risk Indicators (KRIs) against
  their versioned appetite / amber / red thresholds, adverse trends, seasonal-expectation
  deviations, data-quality gaps, and linked incidents; classifies each result PASS/WARN/BREACH
  with cited evidence, deduplicates against open exceptions, checks observation freshness, and
  packages severity-ranked alerts with escalation commentary to human risk queues. Use when a
  scheduled run (or a risk manager / business control officer on demand) needs to surface KRI
  limit breaches, deteriorating trends, off-seasonal readings, stale or missing metric data, or
  breaches tied to open incidents with source-linked evidence. HARD BOUNDARY: this monitor
  ALERTS ONLY — it never accepts a risk, grants a waiver, changes a limit, threshold, or
  appetite, changes a risk or control rating, closes or suppresses an alert, incident, or case,
  files any regulatory report, or writes any system of record. Every disposition is a human
  risk decision.
license: MIT
compatibility: Amazon Quick Desktop; requires read-only risk-register/KRI-library, metric/observation feed, loss-event & incident, scenario, third-party-inventory, and prior-alert MCP integrations (all read-only).
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
  aws-fsi-primary-user: "Risk manager / business control officer"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Key Risk Indicator Monitor

## Purpose and outcome
Given a set of Key Risk Indicators (KRIs) with their latest observations and a **versioned
threshold library** (amber/red bands, direction, seasonal baselines), evaluate every KRI
across five lenses — **threshold band, adverse trend, seasonal-expectation deviation, data
quality, and freshness** — classify each result **PASS / WARN / BREACH**, attach cited
evidence and any linked incidents, deduplicate against already-open exceptions, flag stale or
missing observations, and emit **severity-ranked alerts with escalation commentary** to human
risk queues. A successful run lets a risk manager or business control officer see, with
evidence, exactly which KRIs are breaching appetite, which are deteriorating toward a breach,
which readings are abnormal for the season, which are stale or missing, and what is new since
the last run — so a **human** can adjudicate and escalate. This is a **scheduled, read-only,
alert-only** monitor: it packages exceptions, it does not resolve them.

## Use when
- A scheduled KRI run needs to screen indicators for threshold breaches and near-breaches.
- "Which KRIs are over their amber or red thresholds right now?"
- "Which KRIs are still in appetite but deteriorating several periods in a row?" (trend)
- "Is any reading abnormal versus its seasonal norm even though the absolute value looks OK?"
- "Are any KRIs missing this period's value or running on stale data before the pack goes out?"
- A reviewer wants a consistent, cited exception queue with new-vs-still-open separation and
  escalation commentary linking breaches to open incidents.

## Do not use
- The user wants the monitor to **dispose of** a breach — accept the risk, grant/track a
  waiver, change a limit, threshold, or appetite, or change a risk or control rating → out of
  scope; this monitor alerts only. Route the human to risk governance and the register owner.
- **Deep analysis of the loss/operational event** behind an operational KRI breach →
  `operational-risk-event-analyzer`. **Portfolio-level credit-risk view** behind a credit KRI
  → `credit-risk-portfolio-analyzer`. **Liquidity scenario** behind a liquidity KRI →
  `liquidity-risk-scenario-analyzer`. **Vendor (re)assessment** behind a third-party KRI →
  `third-party-risk-assessor`.
- **Designing a stress scenario** from a deteriorating trend → `stress-test-scenario-designer`.
  **Folding a cluster of breaches into the enterprise/board assessment** →
  `enterprise-risk-assessment-builder`. **Linking a breach to the failing control** →
  `risk-control-self-assessment-assistant`.
- The **threshold or appetite itself changed** (regulation/appetite update) and the library
  must be re-baselined → `regulatory-change-impact-analyzer`.
- Personalized **investment, legal, or accounting advice**, or a **binding risk decision** →
  out of scope; those are human, and where regulated, licensed-specialist, decisions.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a cited exception pack
with a durable `run_id` and per-alert `fingerprint`s; downstream analysis, scenario, and
governance skills consume it. It must not duplicate their disposition or remediation steps,
and it never closes an exception itself.

## Inputs and prerequisites
- One or more **KRIs**, each with `kri_id`, `name`, `category`, `owner`, `unit`, `direction`
  (`higher_is_worse` | `lower_is_worse`), optional `critical` flag, `amber` and `red`
  thresholds, an `observations` history (`{period, value}`), and `observation_as_of`.
- Optional per-KRI **seasonal baseline** (`seasonal_baseline`, `seasonal_tolerance_pct`),
  `trend_min_moves`, `plausible_range`, and `linked_incidents`.
- Run-level `config_version` (the versioned threshold library), `max_staleness_days` for
  freshness, and the **prior open-alert** fingerprints for deduplication. Schema and
  validation: [scripts/validate_input.py](scripts/validate_input.py).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The **KRI / risk-register threshold
library is the definition of record** for every band, direction, and seasonal baseline; the
metric feed is the observation book of record; the loss-event/incident store resolves
linkage. Cite every alert's evidence to a source row and the threshold to its
`config_version`. Never infer a threshold from an observation or an assertion.

## Workflow
1. **Load & validate** — pull the versioned KRI library, latest observations and history, the
   incident linkage, and prior open alerts for the run; validate with `validate_input`.
2. **Check freshness** — compute `staleness_days` per KRI; mark any exceeding
   `max_staleness_days` as stale and raise a freshness alert. Never drop or silently refresh.
3. **Evaluate lenses (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to classify each KRI
   across threshold, trend, seasonal, and data-quality lenses PASS/WARN/BREACH. Each alert
   carries measured value, threshold/expectation, and cited evidence.
4. **Score & route** — map each alert to a deterministic `severity` and routing `queue` per
   the documented mapping ([references/domain-rules.md](references/domain-rules.md)). This is
   a triage suggestion for a human, not a risk determination.
5. **Deduplicate** — fingerprint each alert and split **new** vs **still-open** against the
   prior open-alert baseline so persistent breaches do not re-alert every run.
6. **Package the queue** — emit the alert pack (summary, per-alert evidence, linked incidents,
   escalation commentary, freshness, disclaimer) to the risk queues for human adjudication.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check confirms: every alert is well-formed with cited evidence; severity and
queue tie out deterministically; deduplication partitions new vs still-open; stale KRIs are
flagged (never suppressed); **no autonomous-action / decision language** is present; the
standing disclaimer is present; and escalation counts tie out. Fail closed on any miss.

## Human approval
`required` (R3): mandatory human adjudication before **any** regulated risk decision or
system-of-record change flowing from an alert — accepting a risk, granting a waiver, changing
a limit/appetite, changing a risk or control rating, filing a report, or closing an
incident/case. The scheduled read and the internal alert queue are the monitor's only outputs.
**Every disposition is a human risk decision**; the monitor never performs or recommends one.

## Failure handling
- **Stale observations** (older than `max_staleness_days`) → flag the KRI, mark its alerts
  `stale_input`, treat results as low-confidence; do not present as current.
- **Missing / null latest observation** → raise a data-quality alert (not a false all-clear);
  do not evaluate thresholds on a value that is not there.
- **Missing / ambiguous threshold** → report the gap; never invent or guess a band.
- **Insufficient history** for the trend or seasonal lens → skip that lens for the KRI and say
  so; do not fabricate a trend from one or two points.
- **No prior open-alert baseline** → deduplication is disabled; report everything as new and
  say so. **Tool timeout** → return alerts computed so far with an "incomplete" flag; assume
  no automatic retry.

## Output contract
1. **Summary** — run id, as-of, KRIs evaluated, counts (new, deduplicated, warn, breach),
   stale KRIs, and linked incidents.
2. **Alerts** — per alert: KRI id/name/category/owner, breach_type
   (threshold/trend/seasonal/data_quality/freshness), status, measured vs threshold/expectation,
   severity, routing queue, linked incidents, cited evidence, and `is_duplicate` /
   `stale_input` flags.
3. **Escalations** — severity buckets with counts, target queues, and escalation commentary.
4. **Data freshness** — per-KRI staleness and stale flag.
5. **Machine-readable** — alerts + `new_alerts` / `still_open` fingerprints + `run_id`.
6. **Standing disclaimer** — "Monitoring alert only; no risk acceptance, breach waiver, limit
   or appetite change, risk- or control-rating change, incident or case closure, regulatory
   filing, or system-of-record change has been made or recommended. KRI exceptions require
   human risk review and adjudication."
See [references/controls.md](references/controls.md).

## Privacy and records
KRI data can expose **confidential** business, loss, and control information. Minimize the pack
to what evidences an alert. Retain each run's alerts + citations + `config_version` per records
policy; log the read, the queue emission, and any human adjudication recorded downstream. Route
alerts only to approved risk queues; never exfiltrate register or loss data.

## Gotchas
- **An alert is not a decision or an action.** A BREACH justifies *review and escalation*,
  never a monitor-initiated risk acceptance, waiver, limit change, rating change, or closure.
- **Direction matters.** A KRI can be `higher_is_worse` (e.g., delinquency rate) or
  `lower_is_worse` (e.g., Liquidity Coverage Ratio); the engine breaches on the adverse side of
  the red band per the configured `direction`, never on the raw number alone.
- **Boundary bands.** A value exactly on the red limit is an at-limit **WARN**, not a BREACH —
  the engine breaches only when strictly beyond red (or strictly under a floor).
- **Trend is an early warning, not a breach.** An adverse trend fires only while the KRI is not
  already red; once red, the threshold breach already carries the escalation.
- **Seasonality is an extra lens.** A reading can be within absolute appetite yet far outside
  its seasonal norm — the seasonal alert catches that; do not silence it because the number
  "looks fine".
- **Stale or missing data is dangerous.** A "green" run over stale or missing observations can
  hide a live breach — always surface staleness and data-quality gaps rather than a false
  all-clear.
- **Thresholds are versioned config, not judgement.** Never tune a band to a metric or infer
  "what's acceptable here"; cite the threshold and its `config_version`.
