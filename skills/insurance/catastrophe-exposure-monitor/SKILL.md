---
name: catastrophe-exposure-monitor
description: >-
  Scheduled, read-only catastrophe-exposure monitor for insurers. Each run reads the in-force
  portfolio (policies and insured locations), current event footprints (hurricane, wildfire,
  earthquake, flood, severe-convective), and modeled-loss data, then computes zone
  accumulations, single-location and modeled-loss threshold breaches, source freshness, data
  gaps, and suggested response priorities — deduplicated against the prior run and packaged as
  an alert queue for a catastrophe-risk / portfolio manager. Use when a scheduled monitor
  should watch exposure against an active or forecast event, refresh accumulation and PML
  alerts, flag stale feeds, deduplicate ongoing alerts, or queue breaches for human review.
  HARD BOUNDARY: it only alerts and queues — it NEVER binds or declines coverage, changes
  limits or capacity, buys or cedes reinsurance, adjusts reserves, issues endorsements, closes
  or suppresses alerts, or writes any system of record; every figure is an estimate for a
  human to act on.
license: MIT
compatibility: Amazon Quick Desktop; requires policy-administration, claims, catastrophe-event-feed, actuarial/catastrophe-model, document-intelligence, and reference/geocode MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Insurance"
  aws-fsi-skill-type: "System-interaction or operational skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Monitor & alert"
  aws-fsi-agent-pattern: "Scheduled monitor + human queue"
  aws-fsi-delivery-wave: "Wave 2 - analytical production"
  aws-fsi-action-mode: "Scheduled read-only; alert only"
  aws-fsi-scheduled-agent: "read-only-monitoring"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Insurance underwriting & claims"
  aws-fsi-primary-user: "Catastrophe risk / portfolio manager"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Catastrophe Exposure Monitor

## Purpose and outcome
A **scheduled, read-only** monitor that, on each run, joins the in-force portfolio to the
current event footprints and modeled-loss data, computes **explainable exposure metrics**
(zone accumulation, single-location, event modeled-loss range), compares them to versioned
thresholds, deduplicates against the prior run, and packages **cited alerts** for a human
review queue with a suggested response priority. A successful run lets a catastrophe-risk /
portfolio manager see, in one place, which zones/events breach appetite, what is new vs
ongoing vs cleared, which feeds are stale, and where data gaps limit confidence — so a
**human** decides the response. The monitor never acts, decides, or closes.

## Use when
- A scheduled job should watch portfolio exposure against an **active or forecast** event.
- "Refresh the accumulation and PML alerts for the current hurricane / wildfire / quake."
- "Which zones are over appetite for this event, and what's new since the last run?"
- A manager needs a **deduplicated, cited** alert queue with stale-feed and data-gap flags.

## Do not use
- The user wants an **underwriting, capacity, or reinsurance decision or action** (bind,
  decline, change a limit, place/cede reinsurance) → out of scope; flag the exposure and
  route to the human queue / `underwriting-workbench-assistant` (a licensed underwriter acts).
- **Reserving / IBNR** off an event's modeled loss → `reserving-analysis-assistant`.
- **Treaty attachment / retention / recovery** interpretation → `reinsurance-treaty-interpreter`.
- **Claims surge triage** after landfall → `claims-triage-assistant`.
- New-submission intake screening in a stressed zone → `submission-intake-triager`.
- One-off, interactive "explain this policy's exposure" with no monitoring/threshold context
  → an interactive analysis skill, not this scheduled monitor.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This monitor emits an alert package with
a durable `run_id` and stable `alert_key`s; downstream underwriting / reinsurance / reserving
/ claims skills consume it. It must not duplicate their decisions or actions. Buying capacity
or reinsurance is a human/committee decision — never an invented skill and never an action here.

## Inputs and prerequisites
- **Exposure snapshot** (one run): `as_of`, `config_version`, `sources[]` with timestamps,
  `events[]` (event_id, peril, footprint_zones, footprint_as_of), `locations[]`
  (location_id, policy_id, zone, peril_exposed, tiv, limit, geocoded, valuation_date,
  modeled_loss{low,mid,high}, source_ref), `prior_alerts[]` (last run's alert keys for
  dedup), and `config{}` thresholds. Schema: [scripts/validate_input.py](scripts/validate_input.py).
- Read access to policy administration, the event feed, the cat model, and reference/geocode
  data; the versioned cat-risk config (see [references/domain-rules.md](references/domain-rules.md)).

## Source hierarchy
See [references/source-map.md](references/source-map.md). Policy administration is the
position of record for exposure; the event feed is the position of record for the hazard
footprint; the cat model supplies modeled-loss estimates. Cite every breach to its location
rows (or the event modeled-loss row). Never substitute a modeled figure for the recorded
limit/TIV; if feed and model footprints disagree, cite both and flag.

## Workflow
1. **Load & validate** — take the run snapshot; run `validate_input` (fails closed on
   structural problems; warns on ungeocoded/unmodeled/stale-valuation gaps).
2. **Freshness check** — for each source compute age vs `max_source_staleness_hours`; mark
   `fresh|stale`; a stale source sets run `confidence: degraded`. Never trust an old footprint.
3. **Compute metrics (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): per event, find
   exposed geocoded locations; compute zone accumulation, single-location, and event
   modeled-loss (low/mid/high); derive each breach's `exceedance_ratio`, `severity` band, and
   `suggested_response_priority`. Metrics are explainable, not an opaque score.
4. **Deduplicate** — assign each breach a stable `alert_key`; classify **new / ongoing /
   cleared** against `prior_alerts`; tie the `dedup` summary to the alerts.
5. **Package the queue** — assemble cited alerts + freshness report + data gaps + dedup
   summary + overall severity + disclaimer, routed to the review queue. Raise alerts; do not act.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check confirms: freshness handled (every source has a status; stale →
degraded); dedup complete (stable keys, valid status, no duplicates, summary ties);
escalation/queue packaging (queue target, cited evidence, and severity/priority equal to the
deterministic mapping from the ratio); and **no autonomous action** (bind/decline/cede/
cancel/endorse/reserve/limit-change/closure language) with the disclaimer present. Fail closed
on any miss.

## Human approval
`external-delivery`: human approval required before the alert package is distributed outside
the review queue or written to a system of record. No approval is needed for the monitor's own
scheduled read + queue. The monitor never takes an underwriting, reinsurance, reserving, or
policy action.

## Failure handling
- **Stale event feed / model** → still report breaches but set `confidence: degraded` and
  flag the stale source; do not treat an old footprint as current.
- **Ungeocoded / unmodeled exposed locations** → exclude from the affected metric and report
  as data gaps; never silently drop exposure.
- **Missing config** → use documented defaults but record that the `config_version` is
  unresolved; thresholds are never guessed per event.
- **Ambiguous event/zone mapping** → cite the conflicting footprints and flag; do not
  reconcile silently.
- **Tool timeout / large portfolio** → page as resumable stages and return the metrics
  computed so far with a clear "incomplete" flag; never assume automatic retries.

## Output contract
1. **Run summary** — `run_id`, `as_of`, `config_version`, queue, `confidence`, overall severity.
2. **Sources** — per source: `as_of`, age, staleness limit, `fresh|stale`.
3. **Alerts** — per alert: `alert_key`, event, zone, peril, `breach_type`, metric vs
   threshold, `exceedance_ratio`, `severity`, `suggested_response_priority`, queue, cited
   evidence, and `status` (new/ongoing/cleared).
4. **Dedup summary** — new / ongoing / cleared counts (tie to alerts).
5. **Data gaps** — ungeocoded, stale-valuation, unmodeled locations.
6. **Standing disclaimer** — "Monitoring alert only; exposure and modeled-loss figures are
   estimates for human review. No underwriting, reinsurance, capacity, reserving, or
   system-of-record action has been taken."
See [references/controls.md](references/controls.md).

## Privacy and records
Customer NPI/PII. Mask policyholder identifiers; carry only the location/policy references
needed to evidence a breach. Retain the run package + citations + config version per records
policy; log each read and any external-delivery approval. Never exfiltrate portfolio or
location data.

## Gotchas
- **An alert is not a decision.** A Critical band justifies *queue urgency*, never a bind,
  a reinsurance placement, or a capacity move — those are human/committee actions.
- **Clearing ≠ closing.** "Cleared" means the metric fell below threshold this run; it is not
  a disposition, and the monitor never closes or suppresses an alert.
- **Ungeocoded locations understate accumulation.** They are excluded from the metric on
  purpose and surfaced as gaps — do not let a clean-looking accumulation hide them.
- **Modeled loss is a range.** Report low/mid/high and the confidence flag; never present the
  tail (or any point) as certain.
- **Stale footprints lie.** An old event feed can make a moving storm look benign; the
  freshness gate and `degraded` confidence exist for this reason.
- **Config, not intuition.** Zone limits, single-location max, and appetite come from the
  versioned config; never tune them inside a run to make a breach disappear.
