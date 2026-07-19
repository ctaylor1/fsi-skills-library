---
name: payment-fraud-case-investigator
description: >-
  Investigate a payment-fraud alert (card CNP, wire, RTP, ACH, account-takeover, mule) by
  resolving the parties and assembling device, identity, behavior, transaction, beneficiary,
  and network evidence into a durable-case-ID evidence bundle with a time-ordered chronology,
  a documented fraud-risk score, and a disposition RECOMMENDATION. Use when a fraud
  investigator or payments risk analyst needs to work a referred alert, build the case
  chronology and cited evidence, or produce a review-ready recommendation and route to a
  specialist. This skill NEVER makes a fraud determination, closes a case, blocks or freezes
  an account/beneficiary, reverses or returns a payment, or drafts/files a SAR — it emits
  evidence plus a recommendation, and a human adjudicator decides. Sanctions/adverse-media
  and APP/BEC social-engineering matters route to specialists.
license: MIT
compatibility: Amazon Quick Desktop; requires case-management, fraud-platform, identity/KYC, gateway/processor/acquirer, beneficiary-directory, settlement/ledger, and ISO 20022-parser MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Payments"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Investigate & casework"
  aws-fsi-agent-pattern: "Case agent + evidence bundle"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII; cardholder data)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Payments operations & risk"
  aws-fsi-primary-user: "Fraud investigator / payments risk analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Payment Fraud Case Investigator

## Purpose and outcome
Take a triaged payment-fraud alert and produce an audit-ready **case**: resolve the parties,
gather evidence across the six pillars (device, identity, behavior, transaction, beneficiary,
network), build a time-ordered chronology, compute a documented fraud-risk score, and emit a
durable `case_id` with a fully cited evidence bundle and a disposition **recommendation**.
The outcome is a review-ready case a fraud adjudicator can act on quickly — the substantive
determination, any account/beneficiary block, payment return, closure, and any SAR stay with
the human adjudicator and downstream specialists.

## Use when
- "Investigate this payment-fraud alert / build the case."
- "Assemble the device, identity, transaction, and beneficiary evidence into a chronology."
- "Score this suspected account-takeover / mule case and recommend a disposition."
- "Is there enough evidence to recommend fraud, or do we need more?"

## Do not use
- **Real-time monitoring / alerting** on the live queue → `real-time-payment-risk-monitor`.
- **Fraud determination, case closure, account/beneficiary block, payment reversal/return** →
  refuse; these need the human adjudicator (and, for repair, `payment-repair-assistant`).
- **Sanctions/adverse-media adjudication** → `sanctions-match-adjudicator`.
- **APP scam / BEC social-engineering** investigation → `phishing-and-bec-investigator`.
- **SAR drafting/filing** → `suspicious-activity-report-drafter` (only after human adjudication).
- **Card dispute / chargeback** handling → `chargeback-dispute-packager` / `dispute-operations-assistant`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Triage/monitoring, investigation (this
skill), specialist adjudication, and downstream action are separate control activities with
different entitlements and case states. This skill emits a durable `case_id` + evidence
bundle and must not perform the adjudicator's or specialists' work.

## Inputs and prerequisites
- The alert(s) with `alert_id`, customer/account refs, channel, amount, `opened_at`, the
  triggering transactions, the six evidence pillars, any flags (sanctions/adverse-media,
  APP/BEC), linked/prior fraud cases, and per-source citation refs. Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Read access to case-management, fraud-platform, identity/KYC, transactions, beneficiary
  directory, settlement/ledger, and the ISO 20022 parser.
- The versioned scoring config (`config_version`, `rules_version`).

## Source hierarchy
See [references/source-map.md](references/source-map.md). Case-management is the system of
record for case state and the `case_id`; the fraud platform provides signals but never a
determination. Cite every evidence item. Scoring weights/thresholds are a **versioned
contract**.

## Workflow
1. **Validate & resolve** — run `validate_input`; resolve parties (customer, beneficiary)
   and confirm the six evidence pillars and citations are present; flag gaps.
2. **Build the case (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): emits a durable
   `case_id`, a time-ordered **chronology**, per-pillar **evidence items** (each cited),
   **network links**, a documented **risk score/band**, and a disposition recommendation.
3. **Route where required** — a sanctions/adverse-media flag routes to
   `sanctions-match-adjudicator`; an APP/BEC indicator routes to
   `phishing-and-bec-investigator`. Routing hands over the `case_id`, not a determination.
4. **Recommend (never decide)** — map the band to `recommend-fraud` /
   `recommend-legitimate` / `recommend-elevated-monitoring`; if required evidence is
   incomplete and signals are not decisive, set `needs-evidence` — never clear or confirm by
   guessing over gaps.
5. **Package for adjudication** — present the cited bundle + recommendation + standing note.
6. **Never adjudicate** — no determination, closure, block, return, or filing.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check enforces: durable `case_id` present; disposition is a recommendation
only (no closure/determination/filing state); the bundle's recommendation matches the record;
every evidence item is cited; `risk_band` ties to `risk_score`; and a regex screen rejects
autonomous closure / fraud-determination / block / SAR-filing language. Fail closed on any
miss.

## Human approval
`required`. Every fraud determination, case closure, account/beneficiary block, fund
recovery, payment return, customer commitment, and SAR filing needs the human adjudicator (or
the relevant downstream specialist). This skill proposes and evidences; humans decide.

## Failure handling
- **Incomplete evidence** → `needs-evidence` listing exactly which pillar is missing; do not
  guess to clear or confirm a case.
- **Ambiguous party/entity** → surface for human confirmation; never auto-merge identities.
- **Sanctions/adverse-media or APP/BEC** → route to the specialist; do not adjudicate here.
- **Stale/conflicting sources** → cite both, record the read time, and flag pending postings.
- **Tool timeout** → return the partial bundle with an explicit incomplete flag; assume no
  automatic retry and no step-up authorization.

## Output contract
1. **Caseload view** — per case: durable `case_id`, `risk_band`, disposition
   (`recommend-fraud` | `recommend-legitimate` | `recommend-elevated-monitoring` |
   `needs-evidence` | `route-specialist`), one-line cited rationale.
2. **Evidence bundle** (per recommended/routed case) — chronology, masked parties, per-pillar
   evidence items (each cited), network links, amounts/instruments/channel, risk score/band +
   reasons, recommended disposition + rationale, citations.
3. **Needs-evidence list** — the exact missing pillar(s) per gated case.
4. **Machine-readable** — the case records + bundles keyed by `case_id`.
5. **Standing note** — "Investigation evidence and a disposition recommendation only; no case
   has been closed, no fraud determination has been made, and no filing has been performed.
   Human adjudication is required before any block, closure, filing, or customer commitment."
See [references/controls.md](references/controls.md) and
[references/domain-rules.md](references/domain-rules.md).

## Privacy and records
**Highly Confidential — customer NPI/PII and cardholder data (PCI).** Never emit a full PAN;
mask customer/account/beneficiary identifiers to what evidences the case. Retain the bundle,
chronology, citations, and `config_version`/`rules_version` per records policy; log analyst
identity on every read and recommendation. Fail closed when identity, completeness, source,
version, or authorization is uncertain.

## Gotchas
- **Recommendation ≠ determination.** A `recommend-fraud` is evidence for a human, not a
  finding; the adjudicator confirms, closes, blocks, and files — not this skill.
- **`recommend-legitimate` is not a clearance.** It recommends releasing a hold for human
  review; it never exonerates.
- **Evidence completeness gates clearing.** A low-score case with a missing pillar becomes
  `needs-evidence`, not a clear.
- **Routing hands over, it does not conclude.** Sanctions/adverse-media and APP/BEC go to
  specialists with the `case_id`; do not adjudicate them here.
- **Score is explainable, not a black box.** The band is a documented sum of signal weights
  from a versioned config, recorded for reproducibility.
- **Chronology is evidence.** Order events by time and cite each; a mis-ordered timeline
  misleads the adjudicator.
