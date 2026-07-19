---
name: real-time-payment-risk-monitor
description: >-
  Scheduled, read-only monitor for real-time / instant-payment flows (RTP, FedNow, SEPA
  Instant). Evaluates each sending account and settlement position against versioned velocity,
  per-transaction limit, structuring, mule pass-through, sanctions/watchlist, and
  prefunded-liquidity rules; classifies each PASS/WARN/BREACH with cited evidence, separates
  observed-flow from inflight (a pending payment that would newly breach), deduplicates against
  open alerts, checks feed freshness, and queues severity-ranked alerts to human payments-risk
  reviewers. Use when a scheduled run or a fraud/risk analyst needs to surface velocity spikes,
  mule indicators, limit or structuring patterns, or sanctioned counterparties. HARD BOUNDARY:
  ALERTS ONLY — never blocks, holds, releases, returns, reverses, or repairs a payment; never
  blocks, freezes, or closes an account; never makes a fraud/AML/sanctions determination; never
  files a SAR; never closes a case or writes any system of record. Disposition is a human
  action.
license: MIT
compatibility: Amazon Quick Desktop; requires read-only payment gateway/processor/acquirer, fraud-platform, settlement, network-rules, ISO 20022 parser, case-management, and ledger MCP integrations (all read-only).
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
  aws-fsi-primary-user: "Payments risk / fraud operations"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Real-Time Payment Risk Monitor

## Purpose and outcome
Given a windowed set of **instant-payment events** (per sending account), the settlement
**funding positions** that back them, and a **versioned rule library**, evaluate every
account and position against every configured velocity, per-transaction limit, structuring,
mule pass-through, watchlist / sanctions-screening, and prefunded-liquidity rule; classify
each result **PASS / WARN / BREACH**; attach cited evidence; distinguish observed **`flow`**
breaches from **`inflight`** breaches (a still-pending payment that would newly cross a
threshold); deduplicate against already-open alerts; flag stale feeds; and emit
**severity-ranked alerts** to human payments-risk / fraud queues. A successful run lets a
payments-risk or fraud-operations analyst see, with evidence, exactly which accounts and
positions are breaching (or about to), what is new since the last run, and where to escalate
— so a **human** can review, adjudicate, and act. Because instant payments settle
irrevocably in seconds, this is a **scheduled, read-only, alert-only** monitor: it surfaces
risk fast; it never acts on the payment, the account, or the case.

## Use when
- A scheduled run needs to screen instant-payment flows for velocity spikes and limit hits.
- "Which accounts breached their outbound velocity or per-transaction limit this hour?"
- "Are any payments going to sanctioned / watchlisted counterparties?"
- "Which accounts show mule-style rapid pass-through (fan-in then fan-out)?"
- "Is any prefunded settlement position (RTP/FedNow) approaching its liquidity limit?"
- A reviewer wants a consistent, cited alert queue with new-vs-still-open separation.

## Do not use
- The user wants the monitor to **act** — block/hold/release/return/reverse a payment, block
  or freeze an account, or repair a rejected payment → out of scope; this monitor alerts
  only. Route the human to their entitled fraud / payment-operations tooling, or (for an
  approved repair) to `payment-repair-assistant`.
- **Deep fraud investigation** of a flagged account (device, identity, beneficiary, network)
  → `payment-fraud-case-investigator`. **AML triage / investigation** of a mule or
  laundering pattern → `aml-alert-triager` then `transaction-monitoring-alert-investigator`.
- **Sanctions/watchlist true-match adjudication** → `sanctions-match-adjudicator`.
- **Settlement-liquidity stress modeling** behind a liquidity alert →
  `liquidity-risk-scenario-analyzer`.
- The flag is really an **ISO 20022 message / exception** (pacs reject, camt) rather than a
  risk pattern → `iso-20022-message-interpreter` or `payment-exception-investigator`; a
  failed/delayed payment → `payment-failure-diagnoser`.
- A **fraud/AML/sanctions determination, account decision, SAR filing, or case closure** →
  out of scope; those require human adjudication and entitled systems.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a cited alert pack
with a durable `run_id` and per-alert `fingerprint`s; downstream investigation, adjudication,
scenario, and repair skills consume it. It must not duplicate their disposition, decision, or
remediation steps, and it never closes an alert or case itself.

## Inputs and prerequisites
- One or more **accounts** with `account_id`, feed `as_of`, and windowed `payments` (each
  with `payment_id`, `direction` inbound/outbound, `status` settled/pending, `amount`, and
  where available `counterparty_id`, `counterparty_name`, `scheme`, `timestamp`).
- **Settlement funding positions** with `position_id`, `prefunded_liquidity`, `net_outflow`,
  and optional `pending_outflow` for liquidity checks.
- The **versioned rule set** (`config_version`): velocity (count/amount), per-transaction
  limit, structuring, mule pass-through, watchlist, and liquidity rules with their buffers.
- **Watchlists** (sanctions / fraud / mule) keyed by list name; `max_staleness_minutes` for
  feed freshness; and the **prior open-alert** fingerprints for deduplication. Schema and
  validation: [scripts/validate_input.py](scripts/validate_input.py).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The **rule library and watchlists
are the definition of record** for every threshold and screening entry; the gateway /
processor / fraud-platform feeds are the payment book of record; settlement feeds are the
liquidity book of record. Cite every alert's evidence to a source row and the rule to its
`config_version`. Never infer a limit, a watchlist entry, or a determination from the flow.

## Workflow
1. **Load & validate** — pull the versioned rules, watchlists, windowed payment events,
   settlement positions, and prior open alerts for the run; validate with `validate_input`.
2. **Check freshness** — compute `staleness_minutes` per account/position against the run
   `as_of` and `max_staleness_minutes`; mark any exceeding it stale and raise a freshness
   alert. Never drop or silently refresh a stale feed.
3. **Evaluate rules (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to classify each
   entity×rule PASS/WARN/BREACH, computing both **flow** breaches (observed settled activity)
   and **inflight** breaches (a still-pending payment that would newly breach). Each alert
   carries measured value, limit, and cited evidence.
4. **Score & route** — map each alert to a deterministic `severity` and routing `queue` per
   the documented mapping ([references/domain-rules.md](references/domain-rules.md)). This is
   a triage suggestion for a human, not a fraud/AML/sanctions determination.
5. **Deduplicate** — fingerprint each alert and split **new** vs **still-open** against the
   prior open-alert baseline so a persistent pattern does not re-alert every run.
6. **Package the queue** — emit the alert pack (summary, per-alert evidence, escalations,
   freshness, disclaimer) to the payments-risk queues for human review and adjudication.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check confirms: every alert is well-formed with cited evidence; severity
and queue tie out deterministically; measured rule types carry `measured_value` and `limit`;
deduplication partitions new vs still-open; stale feeds are flagged (never suppressed); **no
autonomous-action / decision / filing / closure language** is present; the standing
disclaimer is present; and escalation counts tie out. Fail closed on any miss.

## Human approval
`required` (R3 decision support): human adjudication is required before **any regulated
decision or action** — a fraud/AML/mule/sanctions determination, an account block/freeze, a
payment hold/release/return/reversal/repair, a SAR or regulatory filing, a case closure, or
any system-of-record write. The scheduled read and the internal alert queue are the monitor's
only outputs. **Every disposition is a human action**; the monitor never performs, decides,
or recommends one as taken.

## Failure handling
- **Stale feeds** (older than `max_staleness_minutes`) → flag the entity, mark its alerts
  `stale_input`, treat results as low-confidence; do not present as current.
- **Missing / ambiguous threshold** → report the gap; never invent or tune a limit.
- **Missing `counterparty_id`** → watchlist / mule-beneficiary screening is not evaluable for
  that payment; label it via input warnings rather than guessing membership.
- **Missing watchlist** → screening rules fire only from rule-level `entries`; say so.
- **No prior open-alert baseline** → deduplication is disabled; report everything as new and
  say so. **Tool timeout** → return alerts computed so far with an "incomplete" flag; assume
  no automatic retry and no step-up authorization.

## Output contract
1. **Summary** — run id, as_of, window, accounts/positions/rules evaluated, counts (new,
   deduplicated, warn, breach), and stale entities.
2. **Alerts** — per alert: entity, rule, scope/bucket, status, breach_type
   (flow/inflight/freshness), measured vs limit, severity, routing queue, cited evidence, and
   `is_duplicate` / `stale_input` flags.
3. **Escalations** — severity buckets with counts and target queues.
4. **Data freshness** — per entity staleness and stale flag.
5. **Machine-readable** — alerts + `new_alerts` / `still_open` fingerprints + `run_id`.
6. **Standing disclaimer** — "Monitoring alert only; no payment, account, or case action has
   been taken … Payment-risk alerts require human review and adjudication, and any regulated
   decision, account action, filing, or case closure is a human action."
See [references/controls.md](references/controls.md).

## Privacy and records
Payment events and counterparties are **Highly Confidential (customer NPI/PII; cardholder
data)**. Minimize data in the pack to what evidences an alert; do not embed full PANs or
unnecessary personal data. Retain each run's alerts + citations + `config_version` per records
policy; log the read, the queue emission, and any human adjudication. Route alerts only to
approved payments-risk queues; never exfiltrate flows, counterparties, or watchlist contents.

## Gotchas
- **An alert is not a decision or an action.** A BREACH justifies *human review*, never a
  monitor-initiated block, hold, reversal, filing, or closure. Instant payments are
  irrevocable — the value of this monitor is speed of *alerting*, not acting.
- **Flow vs. inflight.** A `flow` breach reflects activity that has already settled
  (irrevocable); an `inflight` breach is a still-pending payment that would newly breach — the
  most actionable signal for a human, but the monitor still only flags it. It never holds or
  releases the pending payment.
- **Deduplicate, don't silence.** Still-open items remain visible as open; the fingerprint
  logic prevents re-alerting, not tracking.
- **Stale feeds are dangerous.** A "clean" run over a lagging feed can hide a live mule burst
  — always surface staleness rather than presenting stale results as current.
- **Thresholds and watchlists are versioned config, not judgement.** Never tune a limit to an
  account or infer watchlist membership; cite the rule and its `config_version`.
- **Boundary buckets.** A metric exactly at the limit (e.g., count 20 vs a 20 cap) is WARN,
  not BREACH — the engine breaches only when strictly over.
- **A watchlist hit is a candidate, not a confirmed sanctions match.** Route it to
  `sanctions-match-adjudicator`; the monitor never confirms or clears a match.
