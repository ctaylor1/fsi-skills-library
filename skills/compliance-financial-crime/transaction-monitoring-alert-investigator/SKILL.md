---
name: transaction-monitoring-alert-investigator
description: >-
  Scheduled, read-only monitor that investigates AML transaction-monitoring alerts escalated
  from first-line triage: it evaluates each escalated subject's transactions and
  KYC/counterparty/geography evidence against versioned typology thresholds (structuring, rapid
  pass-through, high-risk geography, velocity, cash intensity), classifies each indicator
  PASS/WARN/BREACH with cited evidence, builds a transaction chronology, deduplicates against
  open cases, checks freshness, and packages a severity-ranked evidence bundle with a recommended
  disposition to human FIU queues. Use when a scheduled run (or an FIU investigator on demand)
  needs a cited investigation package for escalated alerts. HARD BOUNDARY: this monitor ALERTS
  and RECOMMENDS ONLY — it never closes or dispositions a case or alert, never decides or files a
  SAR, never freezes or exits an account, never determines suspicion or intent, and never writes
  any system of record. Every AML disposition and SAR filing is a human FIU decision.
license: MIT
compatibility: Amazon Quick Desktop; requires transaction-monitoring/case, KYC/CDD, core-banking transactions, entity-resolution/network, sanctions & adverse-media screening, and prior-case/SAR-index MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Compliance & Financial Crime"
  aws-fsi-skill-type: "System-interaction or operational skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Monitor & alert"
  aws-fsi-agent-pattern: "Scheduled monitor + human queue"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Scheduled read-only; alert only"
  aws-fsi-scheduled-agent: "read-only-monitoring"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Restricted (AML/BSA — SAR confidentiality; tipping-off controls)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Compliance & Financial Crime (FIU)"
  aws-fsi-primary-user: "AML investigator / FIU analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Transaction Monitoring Alert Investigator

## Purpose and outcome
Given a set of AML alerts **escalated from first-line triage**, their subjects, and a
**versioned typology scenario library**, evaluate each escalated subject's transactions and
supporting KYC/counterparty/geography evidence against every configured typology; classify each
result **PASS / WARN / BREACH**; attach cited evidence; build a transaction **chronology**;
deduplicate against already-open cases; flag stale data; compute a deterministic **recommended
disposition**; and emit a **severity-ranked evidence bundle** to human FIU queues. A successful
run gives an AML/FIU investigator a cited, reproducible investigation package — which typologies
fired, on what evidence, in what sequence, and what is new since the last run — so a **human**
can adjudicate. This is a **scheduled, read-only, alert-only** monitor and **R3 decision
support**: it packages evidence and a recommendation; it never dispositions the case.

## Use when
- A scheduled investigation run needs to work the queue of escalated transaction-monitoring
  alerts and surface typology indicators with evidence.
- "Which escalated subjects show structuring, rapid pass-through, or high-risk-geography flow?"
- "Build the evidence bundle and chronology for this escalated alert for my review."
- "What is new on this subject since the last run, and what remains open?"
- A reviewer wants a consistent, cited indicator set with a recommended (not final) disposition.

## Do not use
- The user wants the monitor to **disposition** the alert — close/clear the case, decide or file
  a SAR, or take an account action → out of scope; this monitor alerts and recommends only.
  Route the human: SAR drafting → `suspicious-activity-report-drafter`; the filing/closure
  decision stays with the FIU and its authorized reviewers.
- **First-line triage** (high-volume prioritization, approved suppression) is upstream →
  `aml-alert-triager`.
- A potential **sanctions match** on the subject/counterparty needs adjudication →
  `sanctions-match-adjudicator`. A **KYC/CDD gap or refresh** → `kyc-customer-due-diligence-screener`.
  **Adverse-media** assessment → `adverse-media-investigator`. The pattern is really **payment
  fraud** (device/identity/beneficiary) → `payment-fraud-case-investigator`.
- **Tuning the typology thresholds** themselves → owned by the financial-crime tuning /
  model-risk function; report the gap, do not adjust a threshold here.
- A **determination of suspicion or legal advice** → out of scope; that is a human FIU decision.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Upstream, `aml-alert-triager` escalates the
alert. This skill emits a cited evidence bundle with a durable `run_id` and per-indicator
`fingerprint`s; downstream SAR drafting, sanctions adjudication, KYC, and adverse-media skills
consume it. It must not duplicate their disposition steps, and it never closes a case or files a
SAR itself.

## Inputs and prerequisites
- One or more **escalated subjects**, each with `subject_id`, `alert_id`, `escalated`,
  `escalation_source`, `risk_rating`, `data_as_of`, a `profile` (with `expected_period_txns`),
  `accounts`, `counterparties`, and a **transaction ledger** (each txn with `txn_id`, `date`,
  `direction` in/out, `amount`, `instrument`, `channel`, `counterparty_id`,
  `counterparty_country`).
- The **versioned typology rule set** (`config_version`): structuring, pass-through, geography,
  velocity, and cash-intensity thresholds with their warn buffers.
- `max_staleness_days` for freshness, and the **prior open-case** fingerprints for
  deduplication. Schema and validation: [scripts/validate_input.py](scripts/validate_input.py).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The **escalated alert and the versioned
scenario library are the definition of record** for what is investigated and against which
thresholds; core banking is the transaction book of record; entity resolution normalizes
counterparties. Cite every indicator's evidence to a source row and the rule to its
`config_version`. Never infer a threshold from the data or an assertion.

## Workflow
1. **Load & validate** — pull the escalated alerts, subjects, versioned rules, and prior open
   cases for the run; validate with `validate_input`. Warn on non-escalated subjects.
2. **Check freshness** — compute `staleness_days` per subject; mark any exceeding
   `max_staleness_days` as stale and raise a freshness indicator. Never drop or silently refresh.
3. **Evaluate typologies (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to classify each
   subject×rule PASS/WARN/BREACH, attach cited evidence, and build the transaction chronology.
4. **Score & recommend** — map each indicator to a deterministic `severity` and routing `queue`,
   and each subject to a deterministic recommended disposition
   ([references/domain-rules.md](references/domain-rules.md)). This is a triage suggestion for a
   human, not an AML determination.
5. **Deduplicate** — fingerprint each indicator and split **new** vs **still-open** against the
   prior open-case baseline so a persistent pattern does not re-alert every run.
6. **Package the bundle** — emit the evidence bundle (summary, per-indicator evidence,
   chronology, recommended dispositions, escalations, freshness, disclaimer) to the FIU queues
   for human adjudication.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py) after.
The output check confirms: every indicator is well-formed with cited evidence; severity and queue
tie out deterministically; deduplication partitions new vs still-open; stale subjects are flagged
(never suppressed); each chronology is date-ordered; each recommended disposition is in the
recommend-only vocabulary and ties out to its indicator counts; **no autonomous decision /
closure / filing language** is present; the standing disclaimer is present; and escalation counts
tie out. Fail closed on any miss.

## Human approval
`required`: human FIU adjudication is mandatory before any regulated outcome — an alert
disposition, a case closure, a SAR filing decision, a customer/account action, or any
system-of-record change. The scheduled read and the internal queue are the monitor's only
outputs. **Every disposition — closure, clearance, SAR filing, or account action — is a human
action**; the monitor never performs or decides one.

## Failure handling
- **Stale data** (older than `max_staleness_days`) → flag the subject, mark its indicators
  `stale_input`, treat results as low-confidence; do not present as current.
- **Missing / ambiguous threshold** → report the gap; never invent or guess a threshold.
- **Missing evidence field** (no `instrument`, `counterparty_country`, or
  `expected_period_txns`) → evaluate only the rules the data supports; label the rest
  not-evaluable via input warnings.
- **Non-escalated subject** → warn; this monitor investigates alerts escalated from first-line
  triage, not the raw alert firehose.
- **No prior open-case baseline** → deduplication is disabled; report everything as new and say
  so. **Tool timeout** → return indicators computed so far with an "incomplete" flag; assume no
  automatic retry.

## Output contract
1. **Summary** — run id, as-of, subjects/rules evaluated, counts (new, deduplicated, warn,
   breach), stale subjects, and recommendation tallies.
2. **Indicators** — per indicator: subject, rule, bucket, status, severity, routing queue,
   measured vs threshold (typology rules), cited evidence, and `is_duplicate` / `stale_input`.
3. **Subjects** — per escalated subject: alert id, risk rating, indicator counts, chronology,
   and a `recommended_disposition` (recommend-only) with rationale.
4. **Escalations** — severity buckets with counts and target queues.
5. **Data freshness** — per subject staleness and stale flag.
6. **Machine-readable** — indicators + `new_alerts` / `still_open` fingerprints + `run_id`.
7. **Standing disclaimer** — "Monitoring alert only; this package is investigative
   decision-support. No case has been closed, no suspicious activity report has been filed or
   decided, no alert has been dispositioned, no account has been frozen or blocked, and no system
   of record has been updated. Every AML disposition, escalation decision, and SAR filing is a
   human FIU decision."
See [references/controls.md](references/controls.md).

## Privacy and records
Customer, transaction, and counterparty data is **Restricted (AML/BSA — SAR confidentiality;
tipping-off controls)**. Minimize data in the bundle to what evidences an indicator. Retain each
run's indicators + evidence + citations + `config_version` per BSA records-retention policy; log
the read, the queue emission, and any required-approval handoff. Route bundles only to entitled
FIU queues; never expose SAR existence or investigative content to the customer or unauthorized
parties, and never exfiltrate customer or transaction data.

## Gotchas
- **An indicator is not a determination or an action.** A BREACH justifies *investigation and
  review*, never a monitor-initiated closure, SAR filing, account action, or "not suspicious."
- **Tipping-off is a real risk.** Never surface SAR existence or investigative content to the
  customer; route only to entitled FIU queues.
- **Deduplicate, don't silence.** Still-open items must remain visible as open; the fingerprint
  logic prevents re-alerting, not tracking.
- **Stale data is dangerous.** A "clean" run over week-old transactions can hide live structuring
  — always surface staleness rather than presenting stale results as current.
- **Thresholds are versioned config, not judgement.** Never tune a threshold to a subject or
  infer "what's acceptable here"; cite the rule and its `config_version`.
- **Recommend, never decide.** `recommended_disposition` is a triage suggestion for the FIU; the
  disposition, closure, and SAR-filing decision are always human.
- **Escalation, not conclusion.** Structuring just under a reporting threshold is a *pattern to
  investigate*, not proof of intent; describe measured vs threshold factually.
