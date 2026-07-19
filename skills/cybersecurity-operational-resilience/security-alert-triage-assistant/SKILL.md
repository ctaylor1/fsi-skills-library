---
name: security-alert-triage-assistant
description: >-
  Triage a batch of security alerts for a SOC analyst or incident responder: enrich each alert
  with asset (CMDB), identity (IAM), threat-intelligence, and vulnerability/cloud-posture
  context; map affected assets and identities; correlate and deduplicate against open cases;
  apply ONLY approved benign-pattern suppression; compute a documented priority; and assemble an
  analyst-ready, source-mapped draft investigation package. Use when a SOC analyst needs to work
  a SIEM/SOAR alert queue, prioritize alerts, enrich and map affected assets/identities, clear
  known-benign noise under approved rules, or prepare investigation context for escalation. HARD
  BOUNDARY: drafts and packages only — never closes/dispositions an alert, declares or closes an
  incident, contains/isolates/blocks/disables any asset or identity, resets credentials,
  suppresses outside approved rules, writes a system of record, or sends the package; every
  security decision and response action stays with the human analyst and IR process.
license: MIT
compatibility: Amazon Quick Desktop; requires SIEM/SOAR, CMDB, IAM, threat-intelligence, vulnerability/cloud-posture, and incident/BCP MCP integrations (all read-only), plus document-intelligence and approved-source retrieval for citations.
metadata:
  aws-fsi-category: "Cybersecurity & Operational Resilience"
  aws-fsi-skill-type: "System-interaction or operational skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Draft & package"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Confidential (security-sensitive)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "CISO / Operational Resilience"
  aws-fsi-primary-user: "SOC analyst / incident responder"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Security Alert Triage Assistant

## Purpose and outcome
Take a raw SIEM/SOAR security-alert queue and marshal it into a controlled, source-mapped
**draft triage package** that a SOC analyst can investigate. For each alert the package
enriches from CMDB (asset), IAM (identity), threat intelligence, and vulnerability/cloud
posture; maps the affected assets and identities; correlates and deduplicates against open
cases; applies **only approved** benign-pattern suppression; computes a **documented** priority;
and assembles analyst-ready investigation context with advisory next steps. The outcome is a
prioritized, audit-ready package queued for human investigation — the alert disposition, any
incident declaration, and any containment or response action stay with the analyst and the
incident-response process. This skill matches [assets/output-template.md](assets/output-template.md).

## Use when
- "Work my SIEM alert queue / triage and prioritize these alerts."
- "Enrich this alert and map the affected assets and identities."
- "Is this alert a duplicate of an open case?"
- "Does this match an approved benign pattern?" (approved suppression only)
- "Prepare the investigation context to escalate this alert."

## Do not use
- To **disposition or close** an alert (true/false-positive verdict) → that is the analyst's call.
- To **declare or close an incident**, or run incident command → `cyber-incident-response-coordinator`.
- To take a **containment/response action** (isolate, disable, block, reset, kill) → never
  automated; the analyst / IR process authorizes and performs it.
- To **investigate** a specific class deeply → `phishing-and-bec-investigator`,
  `identity-access-reviewer`, `vulnerability-prioritization-assistant`,
  `cloud-security-posture-reviewer`, `data-loss-prevention-incident-assistant`.
- Any request to **suppress outside the approved rules, write a system of record, or
  send/submit** → refuse; package and route to a human.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Triage is deliberately separated from
specialist investigation and incident response (different entitlements, evidence depth, and
authority). This skill emits a durable `case_id` + investigation-context bundle and advisory
routes; it must not perform the specialist's work, decide the alert, or act.

## Inputs and prerequisites
- A batch-intake object: `config_version`, `template_version`, `batch_id`, `source_queue`,
  `required_approvals[]`, `recorded_approvals[]`, `priority_config{}`,
  `approved_scanner_sources[]`, `approved_maintenance_windows[]`, `open_cases[]`, and the
  `alerts[]` (each with signature, window, source ref, asset, identity, threat-intel, vuln
  posture, and signal ids). Schema and field list: [scripts/validate_input.py](scripts/validate_input.py).
- Read access to SIEM/SOAR, CMDB, IAM, threat intelligence, vulnerability/cloud posture, and
  incident/BCP systems — all read-only.
- The **approved suppression rule set**, **priority config**, and **output template** are
  versioned config.

## Source hierarchy
See [references/source-map.md](references/source-map.md). SIEM/SOAR is the system of record for
alert/case state and the `case_id`; CMDB for asset criticality; IAM for identity privilege;
threat intelligence and posture for enrichment. **Cite every enriched signal.** An uncited
"present" evidence section is treated as unsupported and fails the output screen.

## Workflow
1. **Validate intake** — run [scripts/validate_input.py](scripts/validate_input.py); fail closed
   on structural problems, warn on enrichment gaps (they force `needs-data`) and on hard-boundary
   / suppression-override indicators.
2. **Enrich & map (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): resolves each alert's
   asset/identity/threat-intel/posture context and maps affected assets and identities, with
   citations.
3. **Correlate & deduplicate** — match against open cases on asset+signature+window; **link**,
   never merge or close. A subset match is an exact duplicate; an overlap is a correlated
   duplicate linked for human review.
4. **Score priority (deterministic)** — compute a documented priority from asset criticality,
   identity privilege, threat-intel severity, exposure, KEV nexus, confidence, and correlation.
   A known-malicious indicator forces `P1` and escalation.
5. **Apply approved suppression only** — if and only if an alert matches an **approved** rule
   (`SUP-DUP-01` exact duplicate, `SUP-SCANNER-01` authorized scanner, `SUP-MAINT-01` maintenance
   window), mark `approved-suppressed` with the rule id and evidence. Anything else is **not**
   suppressible here; a known-malicious indicator overrides suppression.
6. **Package investigation context** — for non-suppressed alerts, assemble the analyst-ready
   bundle (enrichment, asset/identity map, correlated cases, priority, advisory next steps) with
   citations and a durable `case_id`.
7. **Validate output** — run [scripts/validate_output.py](scripts/validate_output.py); fail
   closed on any control breach. Present the package for human investigation; do not send it.
8. **Never decide or act** — no alert closure, incident declaration, containment, or system write.

## Validation loop
Run `validate_input` before and `validate_output` after. The output check enforces: allowed
draft status only; all eleven template sections present; no unsupported claims (present evidence
sections carry citations); only approved suppression rules; escalated alerts carry cited
investigation context; priority ties to the deterministic mapping; required approvals recorded;
hard-boundary consistency; and screens for decision/closure, containment/response, filing/
system-write, and send/submit language. Fail closed on any miss. See
[references/controls.md](references/controls.md) and [references/domain-rules.md](references/domain-rules.md).

## Human approval
`required`. This skill enriches, prioritizes, and packages; a human analyst investigates and
decides. Every alert disposition, every incident declaration/closure, and every containment or
response action require the authorized human role (SOC triage analyst, SOC shift lead / IR
reviewer as configured). Obtaining the recorded approvals is the human step — the draft merely
lists them as pending.

## Failure handling
- **Unresolvable enrichment** (asset not in CMDB, no signal ids) → set `needs-data`, list exactly
  what is missing; do not guess to clear an alert.
- **Active-compromise indicator** → hard boundary: `package_status=blocked`, urgent route to
  `cyber-incident-response-coordinator`; perform no containment.
- **Ambiguous correlation/dedup** → link as *correlated-duplicate* for human confirmation; never
  auto-merge or auto-close.
- **Known-malicious threat intel** → raise priority to `P1`, override suppression, and escalate.
- **Stale/conflicting sources** → cite both with dates/versions and flag the conflict; escalate.
- **Tool timeout / partial data** → return a partial package with an explicit incompleteness flag
  and `needs-data`; assume no automatic retry.

## Output contract
1. **Draft triage package** — the eleven template sections (batch overview, enrichment, asset/
   identity map, correlation/dedup, prioritization, suppression log, investigation context,
   recommended routing, approvals, sources, standing note), each cited, keyed to
   [assets/output-template.md](assets/output-template.md).
2. **Package status** — `ready-for-analyst` | `needs-data` | `blocked` (never a decision).
3. **Per-alert disposition** — `prepared-for-investigation` | `approved-suppressed` | `needs-data`
   | `correlated-duplicate`, with a one-line cited reason.
4. **Investigation-context bundle** (per escalated alert) — enrichment, map, correlation, priority,
   advisory next steps, citations, durable `case_id`.
5. **Suppression log** — rule id + evidence for each `approved-suppressed` item.
6. **Approval ledger** — every required role with status (pending until a human signs).
7. **Machine-readable** — the package JSON keyed by `case_id`.
8. **Standing note** — draft-only; no disposition, incident, containment, system write, or send.

## Privacy and records
**Confidential (security-sensitive).** Restrict distribution to the SOC/IR workflow. Mask asset
names and identity identifiers to what the alert evidences (`asset_ref`, `identity_ref` are
masked). Retain the package, citations, and config/template versions per security-records policy;
log the analyst identity on every read and every package assembly. Treat alert content and
indicators as need-to-know; do not compile personal data beyond the triage scope.

## Gotchas
- **Triage ≠ disposition.** `ready-for-analyst` means "enriched and queued," not "resolved." The
  alert verdict and any incident decision are always a human's.
- **Suppression ≠ closure.** Approved suppression clears *noise* under a named rule and is
  auditable; it never clears a genuine alert, and a known-malicious indicator overrides it.
- **Dedup links, never deletes.** A duplicate points to its parent case; the parent is still worked.
- **Priority is triage, not a verdict.** A `P1` band routes attention; it does not conclude the
  alert is malicious.
- **Hard boundary fails closed.** An active-compromise indicator blocks routine triage and routes
  to incident response — this skill performs no containment.
- **Draft-only.** The package is never sent, submitted, or written to SIEM/SOAR/ticketing;
  delivery and any response action are separate authorized human steps.
