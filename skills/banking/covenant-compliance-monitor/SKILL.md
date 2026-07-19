---
name: covenant-compliance-monitor
description: >-
  Scheduled, read-only monitor that tests commercial credit facilities against the financial,
  negative, and reporting covenants parsed from their credit agreements: it computes each test
  from approved financial spreads, reconciles the borrower compliance certificate against the
  bank's calculation, tracks headroom and trend, classifies each result PASS/WARN/BREACH with
  cited evidence, deduplicates against open exceptions, checks spread freshness, and packages
  severity-ranked alerts to human credit queues. Use when a scheduled run or a portfolio
  manager or credit officer needs to surface covenant breaches, thin headroom, overdue
  deliverables, or certificate discrepancies with an audit-ready trail. HARD BOUNDARY: this
  monitor ALERTS ONLY — it never declares default,
  accelerates or restructures a facility, grants or drafts a waiver or amendment, changes a
  risk rating, notifies the borrower, closes an exception, or writes any system of record.
  Adjudication and remediation are human credit decisions.
license: MIT
compatibility: Amazon Quick Desktop; requires credit-agreement/covenant-library, approved-spread, compliance-certificate, loan-servicing, and prior-alert MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Banking"
  aws-fsi-skill-type: "System-interaction or operational skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Monitor & alert"
  aws-fsi-agent-pattern: "Scheduled monitor + human queue"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Scheduled read-only; alert only"
  aws-fsi-scheduled-agent: "read-only-monitoring"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Banking product & credit operations"
  aws-fsi-primary-user: "Portfolio manager / credit operations / credit risk"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Covenant Compliance Monitor

## Purpose and outcome
Given a set of commercial credit facilities, their **approved financial spreads**, their
borrower **compliance certificates**, and a **versioned covenant library** parsed from each
credit agreement, evaluate every facility against every financial, negative, and reporting
covenant; classify each result **PASS / WARN / BREACH**; reconcile the borrower-reported
values against the bank's independent calculation; attach cited evidence with headroom and
trend; deduplicate against already-open exceptions; flag stale spreads; and emit
**severity-ranked alerts** to human credit queues. A successful run lets a portfolio manager,
credit-operations analyst, or credit-risk officer see, with evidence, exactly which covenants
are breached (or on thin headroom), which deliverables are overdue, and where the certificate
disagrees with the bank's math — so a **human** can adjudicate and remediate. This is a
**scheduled, read-only, alert-only** monitor: it packages exceptions, it does not resolve them.

## Use when
- A scheduled covenant run (typically quarter-end / certificate cadence) needs to screen a
  portfolio for breaches and near-breaches.
- "Which facilities are over their leverage cap or under their coverage floor this quarter?"
- "Did the borrower's compliance certificate tie out to our spread?" (reconciliation)
- "Whose compliance certificate or audited financials are overdue?"
- "Which facilities are on thin headroom or deteriorating toward a breach?"
- A reviewer wants a consistent, cited exception queue with new-vs-still-open separation.

## Do not use
- The user wants the monitor to **resolve** a breach — grant/draft a waiver or amendment,
  declare default, accelerate the facility, or change a risk rating → out of scope; this
  monitor alerts only. Route the human to `loan-servicing-exception-resolver` (staged remedy
  for authorized approval) and, for an escalation memo, `credit-memo-drafter`.
- **Portfolio-level credit-risk** aggregation / early-warning behind an exception →
  `credit-risk-portfolio-analyzer`. **Forward headroom projection** →  `cashflow-forecaster`.
  **Re-spreading** stale or disputed financials → `financial-spreading-assistant`.
- The **covenant definition itself is ambiguous or changed** (an amendment altered a defined
  term or mechanic) → out of scope; a loan-documentation and legal-counsel question to
  re-baseline the covenant library. The monitor never re-interprets legal covenant language.
- Personalized **credit advice** or a credit decision (approve/decline, impair) → out of
  scope; not a lending decision the monitor is licensed to make.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a cited exception pack
with a durable `run_id` and per-alert `fingerprint`s; downstream servicing, memo, risk, and
forecasting skills consume it. It must not duplicate their adjudication or remediation steps,
and it never closes an exception itself.

## Inputs and prerequisites
- One or more **facilities** with `facility_id`, `borrower_id`, `agreement_id`, `test_period`,
  `spread_as_of`, an approved `spread` (`line_items`), optionally a `prior_spread` for trend,
  a `compliance_certificate` (`received_date`, `reported` values), and the facility's
  `covenants`.
- The **versioned covenant library** (`config_version`) for each agreement: `financial`
  covenants (direction, threshold, cushion, and a `formula` over spread line items),
  `negative` covenants (basket line item, threshold), and `reporting` covenants (deliverable,
  due date, received date, grace).
- `max_staleness_days` for spread freshness, and the **prior open-alert** fingerprints for
  deduplication. Schema and validation: [scripts/validate_input.py](scripts/validate_input.py).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The **credit agreement is the
definition of record** for every covenant (its versioned parse is the `config_version`);
approved spreads are the source of the numbers; the compliance certificate is reconciled, not
trusted blindly. Cite every alert's evidence to a spread/certificate row and the covenant to
its `config_version`. Never infer a covenant, mechanic, or threshold from a spread or an
assertion, and never re-interpret ambiguous legal language.

## Workflow
1. **Load & validate** — pull the versioned covenants, approved spreads, certificates,
   deliverable schedule, and prior open alerts for the run; validate with `validate_input`.
2. **Check freshness** — compute `staleness_days` per facility from `spread_as_of`; mark any
   exceeding `max_staleness_days` as stale and raise a freshness alert. Never drop or silently
   refresh.
3. **Evaluate covenants (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to compute each
   financial covenant from the spread, each negative-covenant basket, and each reporting
   deadline; classify PASS/WARN/BREACH; attach measured value, threshold, headroom, and trend.
4. **Reconcile the certificate** — compare the bank-computed value to the borrower-reported
   value for each certified covenant; raise a reconciliation alert when the difference exceeds
   tolerance.
5. **Score & route** — map each alert to a deterministic `severity` and routing `queue` per
   the documented mapping ([references/domain-rules.md](references/domain-rules.md)). This is a
   triage suggestion for a human, not a credit determination.
6. **Deduplicate** — fingerprint each alert and split **new** vs **still-open** against the
   prior open-alert baseline so persistent breaches do not re-alert every run.
7. **Package the queue** — emit the alert pack (summary, per-alert evidence, escalations,
   freshness, disclaimer) to the credit queues for human adjudication.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check confirms: every alert is well-formed with cited evidence; financial
and negative alerts carry measured and threshold; severity and queue tie out deterministically;
deduplication partitions new vs still-open; stale facilities are flagged (never suppressed);
**no autonomous-action / decision language** is present; the standing disclaimer is present;
and escalation counts tie out. Fail closed on any miss.

## Human approval
`required`: human adjudication is mandatory before **any** regulated covenant action or
system-of-record change — declaring default, accelerating/restructuring, granting or drafting
a waiver or amendment, issuing a reservation of rights, changing a risk rating, notifying the
borrower, or closing an exception. The scheduled read and the internal alert queue are the
monitor's only outputs. **Every disposition is a human credit decision**; the monitor never
performs, recommends, or drafts one.

## Failure handling
- **Stale spreads** (older than `max_staleness_days`) → flag the facility, mark its alerts
  `stale_input`, treat results as low-confidence; do not present as current.
- **Missing / ambiguous covenant** → report the gap; never invent or guess a threshold or
  mechanic, and never re-interpret ambiguous legal wording (route to loan-documentation/legal).
- **Missing spread line item** → the affected covenant is not evaluable; label it via input
  warnings and evaluate only the covenants the spread supports (no false PASS).
- **Certificate vs spread conflict** → raise a reconciliation alert citing both values; do not
  resolve silently or overwrite either source.
- **No compliance certificate** → reconciliation is disabled for that facility; say so. **No
  prior open-alert baseline** → deduplication is disabled; report everything as new and say so.
  **Tool timeout** → return alerts computed so far with an "incomplete" flag; assume no retry.

## Output contract
1. **Summary** — run id, as-of, facilities/covenants evaluated, counts (new, deduplicated,
   warn, breach), and stale facilities.
2. **Alerts** — per alert: facility, covenant, covenant_type, status, breach_type
   (financial_test / negative_covenant / reconciliation / reporting / freshness), measured vs
   threshold, headroom, trend, severity, routing queue, cited evidence, and `is_duplicate` /
   `stale_input` flags.
3. **Escalations** — severity buckets with counts and target queues.
4. **Data freshness** — per facility staleness and stale flag.
5. **Machine-readable** — alerts + `new_alerts` / `still_open` fingerprints + `run_id`.
6. **Standing disclaimer** — "Monitoring alert only; no covenant waiver, amendment, reservation
   of rights, default declaration, risk-rating change, borrower notice, or system-of-record
   change has been made or recommended. Covenant exceptions require human credit review and
   adjudication."
See [references/controls.md](references/controls.md).

## Privacy and records
Borrower financials, spreads, and certificates are **Highly Confidential (customer NPI/PII)**.
Minimize data in the pack to what evidences an alert. Retain each run's alerts + citations +
`config_version` per records policy; log the read, the queue emission, and any human
adjudication recorded downstream. Route alerts only to approved credit queues; never exfiltrate
borrower financials or covenant positions.

## Gotchas
- **An alert is not a decision or an action.** A BREACH justifies *review*, never a
  monitor-initiated default declaration, waiver, amendment, risk-rating change, or closure.
- **Reconcile, don't trust.** A borrower certificate reporting compliance does not make a
  facility compliant; the bank's independent calculation from the approved spread governs, and
  a discrepancy is its own alert.
- **Passive vs. active breaches.** A `financial_test` breach may be under a negotiated cure
  period the monitor does not own; a fresh reporting or basket breach is often the sharper
  signal. All are alerts, not actions.
- **Deduplicate, don't silence.** Still-open items must remain visible as open; the fingerprint
  logic prevents re-alerting, not tracking. A cured breach is closed by a human, not the run.
- **Stale spreads are dangerous.** A "clean" run over a two-quarters-old spread can hide a live
  breach — always surface staleness rather than presenting stale results as current.
- **Covenants are versioned config, not judgement.** Never tune a threshold to a borrower or
  re-interpret a defined term; cite the covenant and its `config_version`.
- **Boundary buckets.** A value exactly at the threshold (e.g., 4.00x vs a 4.00x cap) is WARN,
  not BREACH — the engine breaches only when strictly over (or under, for floors).
