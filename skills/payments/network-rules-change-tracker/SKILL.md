---
name: network-rules-change-tracker
description: >-
  Scheduled, read-only monitor that ingests card-network and payment-scheme bulletins (Visa,
  Mastercard, Nacha, RTP), checks each bulletin's authenticity and version, extracts obligations
  and effective dates, maps every obligation to affected products, procedures, controls,
  contracts, systems, and owners, scores implementation readiness against the effective date,
  deduplicates against open items, checks feed freshness, and packages severity-ranked alerts to
  human payments queues. Use when a scheduled run (or a payments compliance / product / operations
  reviewer) needs to surface upcoming or overdue network-rule changes, mapping gaps, unassigned
  owners, or unauthenticated bulletins with cited evidence. HARD BOUNDARY: ALERTS ONLY - it never
  adopts a rule, accepts/closes/files/attests an obligation, changes a
  product/procedure/control/contract/system, marks a change implemented, grants a waiver, closes
  an alert, or writes any system of record. Adjudication and implementation are human.
license: MIT
compatibility: Amazon Quick Desktop; requires card-network/scheme bulletin feed, rule taxonomy, product/process/control/contract/system inventories, owner & implementation-tracker, and prior-alert MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Payments"
  aws-fsi-skill-type: "System-interaction or operational skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Monitor & alert"
  aws-fsi-agent-pattern: "Scheduled monitor + human queue"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Scheduled read-only; alert only"
  aws-fsi-scheduled-agent: "read-only-monitoring"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII; cardholder data)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Payments operations & risk"
  aws-fsi-primary-user: "Payments compliance / product / operations"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Network Rules Change Tracker

## Purpose and outcome
Given a feed of card-network and payment-scheme **bulletins**, a versioned **rule/change
taxonomy**, and the firm's **inventories** (products, procedures, controls, contracts, systems,
owners) plus an **implementation tracker**, evaluate every bulletin: confirm **authenticity and
version**, extract **obligations and effective dates**, map each obligation to the concrete
inventory items it touches, score **implementation readiness** against the effective date,
check **owner traceability**, deduplicate against already-open items, check feed freshness, and
emit **severity-ranked alerts** to human payments queues. A successful run lets a payments
compliance / product / operations reviewer see, with cited evidence, exactly which network-rule
changes are approaching or overdue, which obligations are unmapped or unowned, and which
bulletins could not be authenticated - so a **human** can decide and implement. This is a
**scheduled, read-only, alert-only** monitor: it packages exceptions, it does not resolve them.

## Use when
- A scheduled network-rules run needs to surface upcoming or overdue scheme changes.
- "Which bulletins are within the readiness window (or past their effective date) and still not
  done?"
- "Which obligations aren't yet mapped to a product / procedure / control / contract / system,
  or have no assigned owner?"
- "Did any bulletin fail the authenticity or version check before we act on it?"
- A reviewer wants a consistent, cited exception queue with new-vs-still-open separation.

## Do not use
- The user wants the monitor to **implement or adjudicate** a change - update a procedure,
  control, contract, or system; mark an obligation done; grant a waiver; or close the item ->
  out of scope; this monitor alerts only. Route the human to the impact/gap skills below and
  their entitled systems.
- **Full obligation-to-business/controls/systems impact analysis** and tracking the
  implementation decision -> `regulatory-change-impact-analyzer`.
- **Comparing changed rules against current procedures/operations** to find gaps, conflicts,
  and obsolete steps -> `policy-procedure-gap-analyzer`.
- **Clause-level extraction** of obligations, dates, and renewal terms from the underlying
  member/merchant **contracts** -> `contract-obligation-extractor`.
- Personalized **legal / regulatory advice** on how to comply -> out of scope; not licensed
  advice. Route to a licensed compliance specialist.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a cited exception pack
with a durable `run_id` and per-alert `fingerprint`s; downstream impact-analysis, gap-analysis,
contract-extraction, and evidence-packaging skills consume it. It must not duplicate their
analysis, decision, or implementation steps, and it never closes an item itself. Where no
catalog skill fits, the reviewer routes to the accountable **payments product / operations /
compliance** owner and licensed specialists.

## Inputs and prerequisites
- One or more **bulletins** with `bulletin_id`, `network`, `effective_date`, `source_ref`,
  `signature_verified`, `version`, and `obligations` (each with `obligation_id`, `summary`,
  `domains`, `impacts` by inventory category, `owner`, `required_lead_days`, and
  `implementation` `{status, tracker_ref, target_date}`).
- The firm's **inventories** (`products`, `processes`, `controls`, `contracts`, `systems`) and
  the **owner registry** for mapping and traceability.
- The **versioned taxonomy** (`config_version`): trusted `networks`, `readiness_bands`
  (`critical`/`high`/`medium` days-to-effective), and `min_lead_days`.
- `feed_as_of` + `max_feed_staleness_days` for freshness, and **prior open-alert** fingerprints
  for deduplication. Schema and validation: [scripts/validate_input.py](scripts/validate_input.py).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The **authoritative network bulletin
is the definition of record** for every obligation and effective date; the firm's inventories
and owner registry are the mapping book of record; the tracker is the readiness source. Cite
every alert's evidence to a source row and the taxonomy to its `config_version`. Never infer an
obligation, effective date, or mapping from an unverified bulletin or an assertion.

## Workflow
1. **Load & validate** - pull the bulletin feed, taxonomy, inventories, owner registry,
   implementation tracker, and prior open alerts for the run; validate with `validate_input`.
2. **Check authenticity & freshness** - confirm each bulletin's publisher, signature, and
   version; compute `feed_as_of` staleness against `max_feed_staleness_days`. Flag (never drop)
   unauthenticated bulletins and a stale feed.
3. **Evaluate (deterministic)** - run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to classify each
   obligation across **authenticity, mapping (completeness + applicability), ownership,** and
   **readiness** (days-to-effective vs bands), each carrying measured value and cited evidence.
4. **Score & route** - map each alert to a deterministic `severity` and routing `queue` per the
   documented mapping ([references/domain-rules.md](references/domain-rules.md)). This is a
   triage suggestion for a human, not a compliance determination.
5. **Deduplicate** - fingerprint each alert and split **new** vs **still-open** against the
   prior open-alert baseline so persistent gaps do not re-alert every run.
6. **Package the queue** - emit the alert pack (summary, per-alert evidence, escalations,
   freshness, disclaimer) to the payments queues for human adjudication.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py) after.
The output check confirms: every alert is well-formed with cited evidence; severity and queue
tie out deterministically; readiness alerts carry `days_to_effective` + `effective_date` and
authenticity alerts a `reason`; deduplication partitions new vs still-open; a stale feed is
flagged (never suppressed); alerts from an unauthenticated bulletin are flagged
`unverified_source`; **no autonomous-action / decision / closure / filing language** is present;
the standing disclaimer is present; and escalation counts tie out. Fail closed on any miss.

## Human approval
`required` (R3): human approval is required before any regulated decision, filing, attestation,
customer/network commitment, case closure, control attestation, or system-of-record change, and
before an alert pack is delivered outside the payments compliance / product / operations
function. The scheduled read and the internal queue are the monitor's only outputs. **Every
adjudication and implementation - accepting an obligation, changing a procedure/control/contract/
system, marking a change done, granting a waiver, filing, or closing an item - is a human
action**; the monitor never performs or recommends one.

## Failure handling
- **Unauthenticated bulletin** (untrusted publisher, unverified signature, or missing
  version/source) -> raise an authenticity alert, flag every derived alert `unverified_source`,
  treat as low-confidence; do not present as an in-force obligation.
- **Stale feed** (older than `max_feed_staleness_days`) -> raise a freshness alert and mark all
  alerts `stale_input`; do not present as current.
- **Missing / ambiguous mapping or owner** -> raise the mapping/ownership gap; never invent an
  inventory item, an owner, or a threshold.
- **Missing effective date or implementation status** -> evaluate only what the data supports
  (status defaults to `not_started`); label the rest via input warnings.
- **No prior open-alert baseline** -> deduplication is disabled; report everything as new and
  say so. **Tool timeout** -> return alerts computed so far with an "incomplete" flag; assume no
  automatic retry.

## Output contract
1. **Summary** - run id, as-of, bulletins/obligations evaluated, counts (new, deduplicated,
   warn, breach), unauthenticated bulletins, and stale-feed flag.
2. **Alerts** - per alert: bulletin, network, obligation, category
   (authenticity/mapping/ownership/readiness/freshness), breach_type, status, severity, routing
   queue, cited evidence, and `is_duplicate` / `unverified_source` / `stale_input` flags.
3. **Escalations** - severity buckets with counts and target queues.
4. **Data freshness** - feed staleness and stale flag.
5. **Machine-readable** - alerts + `new_alerts` / `still_open` fingerprints + `run_id`.
6. **Standing disclaimer** - "Monitoring alert only; no network rule was adopted, no obligation
   was accepted, closed, filed, or attested, no product, procedure, control, contract, or system
   was changed, and no system of record was updated. Network-rule changes require human payments
   compliance, product, and operations review and adjudication."
See [references/controls.md](references/controls.md).

## Privacy and records
Bulletins are typically publisher-confidential and inventories can reference customer NPI/PII and
cardholder-data systems. Minimize data in the pack to what evidences an alert; do not embed
cardholder data. Retain each run's alerts + citations + `config_version` per records policy; log
the read, the queue emission, and any required approval. Route alerts only to approved payments
queues; never redistribute a bulletin or inventory outside entitled reviewers.

## Gotchas
- **An alert is not a decision or an action.** An overdue readiness BREACH justifies *review*,
  never a monitor-initiated procedure change, attestation, waiver, or item closure.
- **Authenticity gates trust, not surfacing.** An unverified bulletin's obligations are still
  surfaced (flagged `unverified_source`) so a human checks provenance - they are never silently
  dropped nor treated as in force.
- **Mapping completeness vs. applicability.** A declared domain with no impacts is a
  *completeness* gap; a referenced item absent from inventory is a *dangling* (applicability)
  gap. Both are alerts, not auto-corrections.
- **Readiness is a clock, not a judgement.** Bands are versioned days-to-effective config, never
  tuned per-bulletin; a "complete" obligation is not re-alerted regardless of the clock.
- **Deduplicate, don't silence.** Still-open items must remain visible as open; the fingerprint
  logic prevents re-alerting, not tracking.
- **Boundary bands.** Days-to-effective exactly at a band edge classifies to the tighter band
  (`<=`), and a strictly-past effective date is `overdue` (BREACH), not merely `critical`.
