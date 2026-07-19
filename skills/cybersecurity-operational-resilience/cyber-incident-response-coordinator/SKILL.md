---
name: cyber-incident-response-coordinator
description: >-
  Maintain a single, source-linked cyber-incident coordination record — chronology, IR roles,
  evidence with chain of custody, a decision log, containment/eradication/recovery tasks,
  stakeholder communications, service dependencies, and post-incident actions — and surface a
  suggested severity band plus notification reminders for the incident commander. Use when an
  incident commander or cyber-response team needs to "keep the incident timeline straight",
  "track containment tasks and decisions", "assemble the evidence and comms log", "who owns
  what in this incident", or prepare a reviewer-ready coordination pack during an active
  incident. This skill coordinates and recommends only: it NEVER makes a regulated decision or
  official severity classification, attributes root cause or a threat actor as fact, takes or
  stages a response action (revoke/isolate/patch/restore), closes/resolves the incident, or
  files a breach/regulatory/SAR notification — those are human and authorized-system actions.
license: MIT
compatibility: Amazon Quick Desktop; requires incident/case-management, SIEM/SOAR, IAM, vulnerability/cloud-posture, CMDB, threat-intelligence, and BCP/resilience MCP integrations (all read-only), plus the approved-calculation service.
metadata:
  aws-fsi-category: "Cybersecurity & Operational Resilience"
  aws-fsi-skill-type: "System-interaction or operational skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Domain workflow"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Confidential (security-sensitive)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "CISO / Operational Resilience"
  aws-fsi-primary-user: "Incident commander / cyber-response team"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Cyber Incident Response Coordinator

## Purpose and outcome
During an active cyber incident, keep one authoritative, **source-linked coordination record**:
an ordered chronology, IR role coverage, an evidence register with chain of custody, a decision
log with named human adjudicators, containment/eradication/recovery tasks with owners and due
times, stakeholder communications, service dependencies and impact tolerances, and post-incident
actions. From the `impact` inputs the skill computes a **suggested severity band** and
deterministic **notification reminders**, all routed to humans. A successful output lets the
incident commander see the current state at a glance, spot gaps (unfilled roles, overdue tasks,
pending decisions, incomplete custody), and hand clean evidence to the right investigation,
remediation, reporting, or specialist owner. Every **decision, severity call, closure, and
filing stays human**.

## Use when
- "Keep the incident timeline straight / update the chronology for INC-…"
- "Track containment tasks, owners, and decisions for this incident."
- "Assemble the evidence log and stakeholder comms for the bridge."
- "Who owns what in this incident, and what's overdue or still pending a decision?"
- "Give me a reviewer-ready coordination pack / situation snapshot."

## Do not use
- The user wants a **regulated decision or action**: set official severity, declare/close the
  incident, decide that notification **is/ is not required**, execute a revoke/isolate/patch/
  restore, or file a breach/regulatory report → out of scope; provide the record and route to the
  human / authorized system.
- **Alert triage/enrichment** before an incident is declared → `security-alert-triage-assistant`.
- **Deep investigation** of a specific vector: BEC/phishing → `phishing-and-bec-investigator`;
  data exfiltration/DLP → `data-loss-prevention-incident-assistant`; payment fraud →
  `payment-fraud-case-investigator`.
- **Drafting the regulatory/resilience report** or maintaining registers →
  `operational-resilience-reporter`. **SAR** consideration → `suspicious-activity-report-drafter`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a coordination record with
a durable `coordination_id`; upstream triage/investigation skills escalate into it, and
downstream identity, vulnerability, cloud-posture, reporting, and investigation skills consume its
evidence. It must not duplicate their investigation, remediation, reporting, or closure steps, and
it never invents an owner — regulated calls go to named humans.

## Inputs and prerequisites
- The **incident record**: `incident_id`, `as_of`, `config_version`, `declared_by`, an `impact`
  block, and the sections (roles, chronology, tasks, evidence, decisions, communications,
  dependencies, post-incident actions). Schema: [scripts/validate_input.py](scripts/validate_input.py).
- Read access to incident/case management, SIEM/SOAR, IAM, vulnerability/cloud posture, CMDB,
  threat intel, and the BCP/resilience register; the versioned coordination config (mandatory
  roles, severity mapping, breach-scale threshold) — see [references/domain-rules.md](references/domain-rules.md).
- Data-quality minimums: a non-empty chronology, at least the incident identity fields, and an
  `impact` block; gaps are surfaced as warnings, not silently filled.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The incident/case-management system is
the position of record; SIEM/SOAR, IAM, posture, and CMDB provide corroborating evidence;
threat-intel is context only (never attribution as fact). Cite every chronology entry, evidence
item, and decision to a source. If the record and a system log conflict, cite both and flag it.

## Workflow
1. **Scope & validate** — confirm `incident_id` and `as_of`; load the record; run
   `validate_input`. Resolve structural errors; carry data-quality warnings into the pack.
2. **Normalize (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to order the chronology,
   compute role coverage, open/overdue tasks by phase, evidence custody completeness, decision
   status (pending vs. human-adjudicated), the **suggested severity band** with its basis, and
   **notification reminders**.
3. **Assemble the record** — attach source_refs to every entry; keep `record_status: open`.
4. **Surface gaps & routing** — list unfilled roles, overdue tasks, decisions awaiting a human,
   incomplete custody; name the human/adjacent-skill owner for each decision and reminder.
5. **Write the pack** — plain-language snapshot + the sections + the suggested severity (for the
   IC to confirm) + reminders + the standing disclaimer. Nothing is decided, closed, or filed.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py) after.
The output screen confirms: no autonomous decision/closure/filing/binding-classification language
and no self-attributed executed response action (revoke/isolate/patch/restore/block/quarantine/
contain/disable); `record_status` is not a closed/filed state; every terminal decision names a human `decided_by`;
`severity_suggested` ties out to the deterministic mapping; every evidence item and chronology
entry is source-linked; the standing disclaimer is present. **Fail closed** on any miss.

## Human approval
`required` (R3). Human approval is mandatory before any regulated decision, official severity
classification, notification/filing, customer or regulator commitment, response action, or
incident closure. The skill stages none of these; it maintains a read-only coordination record and
routes each such step to the accountable human or authorized system.

## Failure handling
- **Missing/ambiguous incident identity** → stop and confirm; never coordinate the wrong incident.
- **Empty or unsourced chronology** → surface it; the pack marks unsourced entries not-citable
  rather than presenting them as evidence.
- **Impact block incomplete** → compute the severity band from what is present, record the basis,
  and flag that the band is low-confidence; never guess missing impact.
- **Stale/conflicting sources** → cite both; do not reconcile silently.
- **Tool timeout / partial load** → return the record assembled so far with an explicit
  "incomplete" flag; do not assume retries.
- **Any request to decide, act, close, or file** → refuse and route to the human owner.

## Output contract
1. **Summary** — incident (id), `as_of`, suggested severity band + basis, and the readiness
   counts (roles missing, open/overdue tasks, decisions awaiting a human, custody gaps).
2. **Chronology** — ordered, source-linked entries by phase.
3. **Roles / Tasks / Evidence / Decisions / Communications / Dependencies** — each with owners,
   status, and citations; decisions show adjudicator and pending vs. human-adjudicated.
4. **Notification reminders** — obligations that MAY apply, each routed to a named human/skill.
5. **Post-incident actions** — proposals only.
6. **Machine-readable** — the coordination core + `coordination_id` for downstream skills.
7. **Standing disclaimer** — "Coordination record only; recommendations and evidence for human
   adjudication. No regulated decision, severity classification, incident closure, regulatory
   filing, or system-of-record write has been performed by this skill."
See [references/controls.md](references/controls.md).

## Privacy and records
Confidential (security-sensitive). Minimize sensitive detail — credentials, secrets, exploit
specifics, and raw customer records are referenced by `source_ref`, not copied into the pack.
Preserve chain of custody (never alter evidence). Retain the coordination record + citations +
config version per records policy; log reads and any approval captured at handoff. Never
exfiltrate incident data.

## Gotchas
- **A coordination record is not a decision.** Overdue tasks, a high severity band, or a fired
  reminder justify *escalation to the IC*, never an autonomous decision, closure, or filing.
- **Suggested severity ≠ official severity.** The band is a triage suggestion from the `impact`
  block; the incident commander confirms or overrides it.
- **Reminders are not determinations.** "Breach-notification clocks may apply" routes to legal/
  privacy; it never asserts that notification is (or is not) required.
- **Attribution is not fact.** Threat-actor and root-cause statements are hypotheses until a
  forensic owner establishes them; record them as such.
- **Do not tune the config to the incident.** Mandatory roles, severity mapping, and the
  breach-scale threshold come from the versioned config, not from what "feels" right today.
- **Track, don't touch.** The coordinator records containment/eradication actions; the entitled
  technical team executes them via their own tools.
