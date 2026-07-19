---
name: concentration-risk-monitor
description: >-
  Scheduled, read-only monitor that aggregates exposures across counterparties, sectors,
  geographies, products, technology, cloud and AI providers, and operational dependencies,
  tests each concentration bucket against versioned single-name, sector, geography, product,
  absolute-cap, and diversification-floor limits, classifies each PASS/WARN/BREACH, flags
  proposed exposures that would newly breach, deduplicates against open alerts, checks
  freshness, and queues severity-ranked alerts to human risk queues. Use when a scheduled run
  (or a risk / credit / resilience officer on demand) needs cited concentration breaches,
  single-point provider or operational dependencies, or a proposed exposure that would newly
  breach before onboarding. HARD BOUNDARY: decision support only (R3); it alerts and
  recommends but never confirms a regulated breach, changes or waives a limit, closes a case,
  files a regulatory return, reduces or exits an exposure, terminates a provider, or writes
  any system of record. Disposition is human.
license: MIT
compatibility: Amazon Quick Desktop; requires risk-register/limit-library, exposure & finance data, third-party/operational-dependency inventory, loss-event & scenario, reference-data, and prior-alert MCP integrations (all read-only).
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
  aws-fsi-primary-user: "Enterprise risk / credit risk / resilience officer"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Concentration Risk Monitor

## Purpose and outcome
Given a set of **books** (legal entities, desks, or portfolios), their exposures, an optional
pipeline of **proposed exposures**, and a **versioned limit library**, aggregate exposures
into concentration buckets along every configured dimension — counterparty / counterparty
group, sector, geography, product, technology, cloud / AI provider, and operational
dependency — and test each bucket against its **concentration** (% of a named basis),
**absolute-cap** (notional), and **diversification-floor** (minimum distinct providers)
limits. Classify each result **PASS / WARN / BREACH**, attach cited evidence, project
proposed exposures for a **forward pre-onboarding breach** signal, flag stale feeds,
deduplicate against already-open alerts, and emit **severity-ranked alerts** to human
enterprise-risk queues. A successful run lets a risk / credit / resilience officer see, with
evidence, exactly which concentration limits are breached (or about to be), which single-point
dependencies exist, and what is new since the last run — so a **human** can adjudicate and
act. This is a **scheduled, read-only, alert-only** monitor: it packages exceptions and
recommendations; it does not resolve them.

## Use when
- A scheduled concentration run needs to screen books for limit breaches and near-breaches.
- "Which books are over their single-name, sector, geography, or product limits right now?"
- "Are we over-concentrated on any single cloud / AI provider or operational vendor?" and
  "do we hold enough distinct providers to satisfy the diversification floor?"
- "Would onboarding this counterparty (or migrating this workload) newly breach a limit?"
  (forward pre-onboarding check against proposed exposures).
- A reviewer wants a consistent, cited exception queue with new-vs-still-open separation.

## Do not use
- The user wants the monitor to **act on** a breach — reduce, exit, or hedge an exposure,
  block an onboarding, migrate or terminate a provider, or grant/waive a limit → out of
  scope; this monitor alerts only. Route the human to their risk-remediation workflow and
  entitled systems.
- The user wants a **regulated determination** — "confirm this is a reportable large-exposure
  breach and file the return", close a case, or attest a control → out of scope; those are
  human adjudications (R3).
- **Deeper vendor / operational-resilience assessment** behind a provider-concentration
  alert → `third-party-risk-assessor`. **Credit-portfolio quality / migration / vintage**
  behind a counterparty concentration → `credit-risk-portfolio-analyzer`. **Loss / near-miss
  root cause** for a materialized event → `operational-risk-event-analyzer`.
- **Scenario / stress design or reverse-stress** on a concentration →
  `stress-test-scenario-designer`; **funding / survival-horizon** questions →
  `liquidity-risk-scenario-analyzer`; **market VaR / sensitivity limits** →
  `market-risk-limit-monitor`; **KRI trend monitoring** → `key-risk-indicator-monitor`.
- Rolling the exceptions into an **enterprise risk assessment** or **RCSA** →
  `enterprise-risk-assessment-builder` / `risk-control-self-assessment-assistant`.
- Personalized **investment advice** → out of scope; not licensed advice.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a cited exception pack
with a durable `run_id` and per-alert `fingerprint`s; downstream assessment, analysis,
scenario, and escalation skills consume it. It must not duplicate their assessment or
disposition steps, and it never adjudicates or closes an exception itself.

## Inputs and prerequisites
- One or more **books** with `book_id`, `exposures_as_of`, a `bases` map of named denominators
  (e.g. `total_exposure`, `eligible_capital`), and `exposures` (each with `exposure_id`,
  `amount`, and the dimension fields it carries: `counterparty`, `counterparty_group`,
  `sector`, `geography`, `product`, `cloud_provider`, `ai_provider`, `technology_provider`,
  `operational_dependency`).
- **Proposed exposures** per book for the forward pre-onboarding check (optional).
- The **versioned rule set** (`config_version`): `concentration` (scope + `basis` +
  `limit_pct` + `warn_buffer_pct` + optional `regulatory`), `absolute_cap` (scope +
  `limit_amount`), and `diversification` (scope + `min_count`) limits.
- `max_staleness_days` for freshness, and the **prior open-alert** fingerprints for
  deduplication. Schema and validation: [scripts/validate_input.py](scripts/validate_input.py).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The **limit library is the
definition of record** for every threshold; the exposure/finance systems are the exposure
book of record; the third-party / operational-dependency inventory resolves provider and
dependency scope; reference data resolves classifications. Cite every alert's evidence to a
source row and the rule to its `config_version`. Never infer a limit from exposures or an
assertion.

## Workflow
1. **Load & validate** — pull the versioned limits, exposures, proposed exposures, provider /
   dependency inventory, and prior open alerts for the run; validate with `validate_input`.
2. **Check freshness** — compute `staleness_days` per book; mark any exceeding
   `max_staleness_days` as stale and raise a freshness alert. Never drop or silently refresh.
3. **Aggregate & evaluate (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to aggregate each
   book's exposures into buckets per dimension and classify each bucket×rule PASS/WARN/BREACH,
   computing both **current** breaches and **proposed** (a pipeline exposure would newly
   breach) breaches, plus diversification-floor breaches. Each alert carries measured value,
   limit, basis, and cited evidence (bucket + top contributors + rule).
4. **Score & route** — map each alert to a deterministic `severity` and routing `queue` per
   the documented mapping ([references/domain-rules.md](references/domain-rules.md)). This is
   a triage suggestion for a human, not a risk determination.
5. **Deduplicate** — fingerprint each alert and split **new** vs **still-open** against the
   prior open-alert baseline so persistent breaches do not re-alert every run.
6. **Package the queue** — emit the alert pack (summary, per-alert evidence, escalations,
   freshness, disclaimer) to the enterprise-risk queues for human adjudication.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check confirms: every alert is well-formed with cited evidence, a measured
value, a limit, and a unit; severity and queue tie out deterministically from
`(rule_type, status, breach_type, regulatory)`; deduplication partitions new vs still-open;
stale books are flagged (never suppressed); **no autonomous-action or decision / closure /
filing language** is present; the standing disclaimer is present; and escalation counts tie
out. Fail closed on any miss.

## Human approval
`required` (R3): human adjudication is mandatory before any regulated decision, limit change,
waiver, case closure, regulatory filing, customer commitment, or system-of-record write. The
scheduled read and the internal alert queue are the monitor's only outputs. **Every
disposition — confirming a breach, waiving or changing a limit, reducing an exposure, closing
or filing an exception — is a human action**; the monitor never performs or authorizes one.

## Failure handling
- **Stale feeds** (older than `max_staleness_days`) → flag the book, mark its alerts
  `stale_input`, treat results as low-confidence; do not present as current.
- **Missing / ambiguous limit** → report the gap; never invent or guess a threshold.
- **Missing basis** (a concentration rule's `basis` absent from a book's `bases`) → that rule
  is not evaluable for that book; skip it and surface the gap via input warnings — do not
  substitute another basis.
- **Missing dimension** (an exposure lacks a scope field) → it does not contribute a bucket
  for that dimension; diversification is **not applicable** to a book with zero populated
  buckets in a dimension (no dependency to concentrate).
- **Exposure vs. inventory conflict** (e.g., provider naming) → cite both; do not resolve
  silently.
- **No prior open-alert baseline** → deduplication is disabled; report everything as new and
  say so. **Tool timeout** → return alerts computed so far with an "incomplete" flag; assume
  no automatic retry.

## Output contract
1. **Summary** — run id, as-of, books/rules evaluated, counts (new, deduplicated, warn,
   breach), and stale books.
2. **Alerts** — per alert: book, rule, scope/bucket, status, breach_type
   (current/proposed/freshness), measured vs limit (with unit and basis), severity, routing
   queue, `regulatory` flag, cited evidence, and `is_duplicate` / `stale_input` flags.
3. **Escalations** — severity buckets with counts and target queues.
4. **Data freshness** — per book staleness and stale flag.
5. **Machine-readable** — alerts + `new_alerts` / `still_open` fingerprints + `run_id`.
6. **Standing disclaimer** — "Monitoring alert only; no risk decision, limit change, waiver,
   case closure, regulatory filing, or system-of-record change has been made. Concentration
   exceptions require human risk review and adjudication."
See [references/controls.md](references/controls.md).

## Privacy and records
Exposures, counterparty identities, and provider dependencies are **Confidential**. Minimize
data in the pack to what evidences an alert (bucket totals + top contributors, not full
books). Retain each run's alerts + citations + `config_version` per records policy; log the
read, the queue emission, and any approval to deliver externally or write a record. Route
alerts only to approved enterprise-risk queues; never exfiltrate exposure detail.

## Gotchas
- **An alert is not a decision or an action.** A BREACH justifies *review and adjudication*,
  never a monitor-initiated exposure reduction, limit waiver, case closure, or regulatory
  filing. (R3: decision support only.)
- **Current vs. proposed breaches.** A `current` breach is often market- or drawdown-driven
  and may sit under an approved remediation plan the monitor does not own; a `proposed` breach
  is the forward signal worth catching before a counterparty is onboarded or a workload
  migrated. Both are alerts, not blocks.
- **Diversification is a floor, not a cap.** A single-provider dependency BREACHes the
  diversification floor even when the provider's share is under the concentration cap — a
  distinct resilience concern; do not conflate the two.
- **Basis matters.** A single-name limit measured against **eligible capital** and a sector
  limit measured against **total exposure** are different denominators; cite the basis and
  never substitute one for another to make a number look better.
- **Stale data is dangerous.** A "clean" run over week-old exposures can hide a live
  concentration — always surface staleness rather than presenting stale results as current.
- **Limits are versioned config, not judgement.** Never tune a threshold to a book or infer
  "what's acceptable here"; cite the rule and its `config_version`.
- **Boundary buckets.** A bucket exactly at the limit (e.g., 30.00% vs a 30% cap) is WARN, not
  BREACH — the engine breaches only when strictly over the limit.
