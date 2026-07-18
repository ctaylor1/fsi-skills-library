---
name: aml-alert-triager
description: >-
  Perform first-line triage of transaction-monitoring (AML) alerts: resolve basic data
  issues, deduplicate, prioritize by risk, summarize the evidence, apply ONLY approved
  suppression logic, and package escalations for investigation. Use when an AML/BSA triage
  analyst or FIU needs to work an alert queue, prioritize alerts, clear obvious duplicates
  and approved false-positive patterns, or prepare an escalation to a full investigation.
  This skill NEVER closes a substantive case, files a SAR, exonerates a customer, or
  suppresses an alert outside the approved, documented suppression rules — escalations go
  to transaction-monitoring-alert-investigator with a durable case ID.
license: MIT
compatibility: Amazon Quick Desktop; requires transaction-monitoring/case-management, KYC/customer-risk, transactions, sanctions/adverse-media, and reference-data MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Compliance & Financial Crime"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Investigate & casework"
  aws-fsi-agent-pattern: "Case agent + evidence bundle"
  aws-fsi-delivery-wave: "Wave 3 — regulated casework"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Restricted (AML/BSA — SAR confidentiality; tipping-off controls)"
  aws-fsi-jurisdictions: "US/BSA-FinCEN (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Financial Intelligence Unit (FIU) / AML compliance"
  aws-fsi-primary-user: "AML triage analyst / FIU investigator"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# AML Alert Triager

## Purpose and outcome
Take raw transaction-monitoring alerts and make the queue workable: fix trivial data gaps,
remove duplicates, rank by risk with cited reasons, and either (a) apply an **approved,
documented** suppression rule (logged, reviewable) or (b) assemble a clean **escalation
package** for a full investigation. The outcome is a prioritized queue and audit-ready
escalations — the substantive disposition (and any SAR) stays with the investigator and
compliance approver.

## Use when
- "Work my AML alert queue / prioritize these alerts."
- "Is this alert a duplicate of an existing case?"
- "Summarize the evidence on this alert and package it for escalation."
- "Does this match an approved false-positive pattern?" (approved suppression only)

## Do not use
- **Full investigation** to disposition (deep network/entity analysis, typology
  conclusions) → `transaction-monitoring-alert-investigator`.
- **SAR narrative drafting** → `suspicious-activity-report-drafter` (draft-only, human-filed).
- **Sanctions potential-match adjudication** → `sanctions-match-adjudicator`.
- **Customer risk-rating** recalculation → `customer-risk-rating-reviewer`.
- Any request to **close a substantive case, exonerate, or file** → refuse; escalate.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Triage is deliberately separated from
investigation (different entitlements, evidence depth, and metrics). This skill emits a
durable `case_id` + escalation bundle; it must not perform the investigator's work.

## Inputs and prerequisites
- The alert(s) with rule ID, alerted entity/account, period, and the triggering
  transactions; customer KYC/risk summary; prior alerts/cases for dedup; the **approved
  suppression rule set** (versioned) and priority config. Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Read access to monitoring/case-management, KYC, transactions, sanctions/adverse-media
  flags, and reference data.

## Source hierarchy
See [references/source-map.md](references/source-map.md). Case-management is the system of
record for alert/case state; KYC for customer risk; transactions for activity. Cite every
evidence item. Approved suppression rules and priority mapping are **versioned contracts**.

## Workflow
1. **Validate & normalize** — run `validate_input`; resolve basic data issues (missing
   MCC, unresolved counterparty) via reference data; flag what cannot be resolved.
2. **Deduplicate** — match against open cases/alerts on entity+period+rule; link, do not
   silently drop; a duplicate is *linked to its parent case*, never closed here.
3. **Score priority (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): computes a
   documented priority from customer risk, amounts, typology hints, sanctions/adverse-media
   proximity, and velocity. Explainable inputs, not a black box.
4. **Apply approved suppression only** — if and only if an alert matches an **approved**
   suppression rule (exact duplicate, whitelisted internal transfer, documented seasonal
   false-positive), mark `approved-suppressed` with the rule ID and evidence. Anything else
   is **not** suppressible here.
5. **Package escalation** — for non-suppressed alerts, assemble the evidence bundle
   (chronology, parties, amounts, KYC/risk, flags) with citations and a durable `case_id`,
   set state `escalate-to-investigation`, and record the recommended priority.
6. **Never close** — no substantive closure/exoneration/filing.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. Output check enforces: only approved suppression codes used; no closure/exoneration/
filing language; escalation bundle complete and cited; priority ties to the deterministic
mapping; SAR-confidentiality / tipping-off language screen. Fail closed on any miss.

## Human approval
`required`. Approved suppression is a **logged, reviewable** action bounded by the approved
rule set; anything beyond it — and every escalation disposition, closure, or filing — needs
the investigator/compliance approver. This skill proposes and packages; humans decide.

## Failure handling
- **Unresolvable data** → set `needs-data`, list exactly what's missing; do not guess to
  clear an alert.
- **Ambiguous entity/dedup** → link as *possible duplicate* for human confirmation; never
  auto-merge or auto-close.
- **Sanctions/adverse-media proximity** → raise priority and route; do not adjudicate here.
- **Stale/conflicting sources** → cite both; escalate.
- **Tool timeout** → return partial triage with an explicit incomplete flag; no retry
  assumption.

## Output contract
1. **Queue view** — per alert: `case_id`, priority band, disposition
   (`escalate-to-investigation` | `approved-suppressed` | `needs-data` | `possible-duplicate`),
   one-line cited reason.
2. **Escalation bundle** (per escalated alert) — chronology, parties (masked), amounts,
   instruments, KYC/risk, sanctions/adverse-media flags, linked cases, citations.
3. **Suppression log** — rule ID + evidence for each `approved-suppressed` item.
4. **Data gaps / needs-data list.**
5. **Machine-readable** — the triage records + bundles keyed by `case_id`.
6. **Standing note** — "First-line triage only; no case has been closed, no customer
   exonerated, and no SAR filed."
See [references/controls.md](references/controls.md).

## Privacy and records
**Restricted — AML/BSA.** SAR-confidentiality applies: never disclose SAR existence/intent
to the customer or unauthorized parties (**tipping-off**). Mask account/customer identifiers
in output to what evidences the alert. Retain triage records + citations + rule/config
versions per BSA recordkeeping. Log every read, suppression, and escalation with the analyst
identity.

## Gotchas
- **Suppression ≠ closure.** Approved suppression clears *noise* under a named rule and is
  auditable; it is not a substantive disposition and must never be used to clear a genuine
  alert.
- **Dedup links, never deletes.** A duplicate points to its parent case; the parent still
  gets worked.
- **Tipping-off is a legal risk.** Do not draft customer-facing text that reveals monitoring
  or SAR activity.
- **Priority is triage, not typology.** Naming a typology hint for routing is fine;
  concluding the typology is the investigator's job.
- **Approved rule set is versioned.** Record the rule/config version on every suppression so
  the decision is reproducible and reviewable.
