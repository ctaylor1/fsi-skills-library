---
name: surveillance-alert-triager
description: >-
  Perform first-line triage of trade- and electronic-communications surveillance alerts:
  resolve basic data issues, deduplicate, prioritize by risk, summarize the evidence into a
  durable-case-ID bundle, apply ONLY approved suppression logic, and package escalations for
  investigation. Use when a surveillance/market-conduct triage analyst needs to work an
  alert queue, prioritize alerts, clear obvious duplicates and approved false-positive
  patterns, or prepare an escalation to a full surveillance investigation. This skill NEVER
  closes a substantive case, makes a market-abuse / manipulation / insider-trading
  determination, exonerates a subject, files a regulatory report, or suppresses an alert
  outside the approved, documented suppression rules — escalations go to
  market-surveillance-alert-investigator with a durable case ID.
license: MIT
compatibility: Amazon Quick Desktop; requires surveillance/case-management, OMS/EMS, communications-archive, market/reference-data, and account-context MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Capital Markets"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Investigate & casework"
  aws-fsi-agent-pattern: "Case agent + evidence bundle"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Capital Markets operations & compliance"
  aws-fsi-primary-user: "Compliance surveillance triage analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Surveillance Alert Triager

## Purpose and outcome
Take raw trade- and e-comms-surveillance alerts and make the queue workable: fix trivial
data gaps, remove duplicates, rank by risk with cited reasons, and either (a) apply an
**approved, documented** suppression rule (logged, reviewable) or (b) assemble a clean
**escalation package** for a full investigation. The outcome is a prioritized queue and
audit-ready escalations, each with a durable `case_id` and an evidence bundle (chronology,
parties, amounts, citations) — the substantive disposition (and any determination, closure,
or filing) stays with the investigator and compliance approver.

## Use when
- "Work my surveillance alert queue / prioritize these alerts."
- "Is this trade or e-comms alert a duplicate of an existing case?"
- "Summarize the evidence on this alert and package it for escalation."
- "Does this match an approved false-positive / calibration pattern?" (approved suppression only)

## Do not use
- **Full investigation** to disposition (deep order-book reconstruction, comms context,
  scenario conclusions) → `market-surveillance-alert-investigator`.
- **E-comms disclosure / supervision / retention** review → `communications-compliance-reviewer`.
- **Execution-quality / routing / venue** question → `best-execution-reviewer`.
- **Personal-account-dealing / cross-side conflict** question → `conflicts-of-interest-reviewer`.
- Any request to **close a case, determine market abuse, exonerate, or file** → refuse; escalate.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Triage is deliberately separated from
investigation (different entitlements, evidence depth, and metrics). This skill emits a
durable `case_id` + evidence bundle; it must not perform the investigator's work. Substantive
disposition, closure, and any regulatory filing are human-adjudicated downstream.

## Inputs and prerequisites
- The alert(s) with scenario ID, alerted entity/account/desk, `surveillance_type`
  (`trade`|`ecomms`), period, and the triggering evidence (orders/executions or messages);
  account/desk risk context; prior alerts/cases for dedup; the **approved suppression rule
  set** (versioned) and priority config. Schema: [scripts/validate_input.py](scripts/validate_input.py).
- Read access to surveillance/case-management, OMS/EMS, communications archive,
  market/reference data, account context, and restricted-list/watch-list flags.

## Source hierarchy
See [references/source-map.md](references/source-map.md). Case-management is the system of
record for alert/case state; OMS/EMS and the communications archive supply evidence; account
context supplies risk and list membership. Cite every evidence item and every chronology
event. Approved suppression rules and priority mapping are **versioned contracts**.

## Workflow
1. **Validate & normalize** — run `validate_input`; resolve basic data issues (unresolved
   instrument/issuer, missing desk context) via reference data; flag what cannot be resolved.
2. **Deduplicate** — match against open cases/alerts on entity+scenario+period; link, do not
   silently drop; a duplicate is *linked to its parent case*, never closed here.
3. **Score priority (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): computes a
   documented priority from account/desk risk, notional, scenario-severity hint,
   cross-product linkage, restricted-list proximity, and velocity. Explainable inputs, not a
   black box.
4. **Apply approved suppression only** — if and only if an alert matches an **approved**
   suppression rule (exact duplicate, whitelisted known-benign accounts, documented
   calibration pattern), mark `approved-suppressed` with the rule ID and evidence. A
   restricted-list / watch-list proximity flag **overrides** suppression and forces
   escalation. Anything else is **not** suppressible here.
5. **Package escalation** — for non-suppressed alerts, build the evidence bundle
   (deterministic chronology with cited events, parties, notional, account/desk risk, flags)
   with a durable `case_id`, set state `escalate-to-investigation`, and record the
   recommended priority. Flag the e-comms disclosure aspect to comms compliance where relevant.
6. **Never determine or close** — no substantive closure, market-abuse determination,
   exoneration, or filing.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. Output check enforces: durable `case_id` on every record; only approved suppression
codes used; escalation bundle complete, cited, and with each chronology event cited;
disposition is a recommendation only; no closure/determination/filing language; priority
ties to the deterministic mapping. Fail closed on any miss.

## Human approval
`required`. Approved suppression is a **logged, reviewable** action bounded by the approved
rule set; anything beyond it — and every escalation disposition, closure, determination, or
filing — needs the investigator/compliance approver. This skill proposes and packages;
humans decide.

## Failure handling
- **Unresolvable data** → set `needs-data`, list exactly what's missing; do not guess to
  clear an alert.
- **Ambiguous entity/dedup** → link as *possible duplicate* for human confirmation; never
  auto-merge or auto-close.
- **Restricted-list / watch-list proximity** → raise priority to P1 and escalate; do not
  adjudicate here.
- **Stale/conflicting sources** → cite both; escalate.
- **Tool timeout** → return partial triage with an explicit incomplete flag; no retry
  assumption.

## Output contract
1. **Queue view** — per alert: `case_id`, priority band, disposition
   (`escalate-to-investigation` | `approved-suppressed` | `needs-data` | `possible-duplicate`),
   one-line cited reason.
2. **Evidence bundle** (per escalated alert) — durable `case_id`, cited chronology, parties
   (masked), notional/instruments, account/desk risk, restricted-list/watch-list flags,
   linked cases, citations, recommended priority.
3. **Suppression log** — rule ID + evidence for each `approved-suppressed` item.
4. **Data gaps / needs-data list.**
5. **Machine-readable** — the triage records + bundles keyed by `case_id`.
6. **Standing note** — "First-line triage only; no case has been closed, no determination of
   market abuse has been made, and nothing has been filed."
See [references/controls.md](references/controls.md).

## Privacy and records
**Highly Confidential (customer NPI/PII).** Surveillance evidence may include MNPI and
personal communications; handle need-to-know and never tip the subject. Mask
account/desk/party identifiers to what evidences the alert. Retain triage records, suppression
logs, and citations with rule/config versions per the firm's surveillance recordkeeping
standard. Log every read, suppression, and escalation with the analyst identity.

## Gotchas
- **Suppression ≠ closure.** Approved suppression clears *noise* under a named rule and is
  auditable; it is not a substantive disposition and must never be used to clear a genuine
  alert.
- **Naming a scenario is not concluding it.** A scenario hint (spoofing, MNPI-adjacent) is
  for routing/priority; determining market abuse is the investigator's job under human
  adjudication.
- **Dedup links, never deletes.** A duplicate points to its parent case; the parent still
  gets worked.
- **Restricted-list proximity overrides suppression.** Even an otherwise-suppressible alert
  escalates when the subject is watch/restricted-listed.
- **Approved rule set is versioned.** Record the rule/config version on every suppression so
  the decision is reproducible and reviewable.
