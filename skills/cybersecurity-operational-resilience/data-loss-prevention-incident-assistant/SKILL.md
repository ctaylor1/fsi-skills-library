---
name: data-loss-prevention-incident-assistant
description: >-
  Assemble a DRAFT incident-assessment package from a batch of data-loss-prevention (DLP)
  events for a DLP/privacy/incident-response analyst: enrich each event, classify the data
  with a deterministic taxonomy, estimate exposure (egress, trust, magnitude, whether
  regulated data left the perimeter), correlate and deduplicate against open cases, apply ONLY
  approved suppression, compute a documented severity, and preserve evidence references. Use
  when an analyst must investigate potential data exfiltration or DLP policy violations,
  quantify exposure, or package an incident for escalation. HARD BOUNDARY: drafts and packages
  only — never determines or declares a breach, decides or issues a notification, dispositions
  or closes an incident, contains (blocks/revokes/deletes/recalls) any transfer, account, or
  data, suppresses outside approved rules, writes a system of record, or sends the package;
  every breach determination, notification, and response action stays with the human
  privacy/IR owner and legal/compliance.
license: MIT
compatibility: Amazon Quick Desktop; requires DLP console/SIEM-SOAR, IAM, CMDB, web/mail/egress proxy, threat-intelligence, data-classification, and incident/BCP MCP integrations (all read-only), plus document-intelligence and approved-source retrieval for citations.
metadata:
  aws-fsi-category: "Cybersecurity & Operational Resilience"
  aws-fsi-skill-type: "Artifact-creation skills"
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
  aws-fsi-primary-user: "DLP / privacy / incident-response analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Data-Loss-Prevention Incident Assistant

## Purpose and outcome
Take a batch of DLP events (potential data exfiltration or policy violations) and marshal them
into a controlled, source-mapped **draft incident-assessment package** that a DLP/privacy/
incident-response analyst can act on. For each event the package enriches from IAM (actor),
CMDB (asset), and the egress proxy (destination); **classifies the data involved** with a
deterministic taxonomy; **estimates exposure** (egress completed, destination trust, record/
volume magnitude, whether regulated data left the perimeter); correlates and deduplicates
against open cases; applies **only approved** benign/business suppression; computes a
**documented** severity; and **preserves evidence references** for chain-of-custody. The
outcome is a review-ready, audit-ready package queued for human adjudication — the breach
determination, any notification, the incident disposition, and any containment stay with the
privacy/incident-response owner and legal/compliance. This skill matches
[assets/output-template.md](assets/output-template.md).

## Use when
- "Investigate these DLP events / assess this potential data exfiltration."
- "Classify the data in this event and estimate how much left the perimeter."
- "Preserve the evidence and package this DLP incident for escalation."
- "Is this event a duplicate of an open case?"
- "Does this match an approved benign / sanctioned-business pattern?" (approved suppression only)

## Do not use
- To **determine or declare a data breach**, or decide/issue a **regulatory or customer
  notification** → privacy officer + legal/compliance (human); this skill only estimates
  exposure and preserves evidence to inform them.
- To **disposition or close** a DLP incident (confirmed-exfiltration or benign verdict) → the
  analyst/privacy owner decides.
- To take a **containment/response action** (block, quarantine, revoke access, disable an
  account, delete/recall data) → never automated; the IR process authorizes and performs it.
- To **declare or run incident command** → `cyber-incident-response-coordinator`.
- To **investigate a specific vector** deeply → `phishing-and-bec-investigator`,
  `identity-access-reviewer`, `cloud-security-posture-reviewer`, `third-party-cyber-risk-reviewer`.
- Any request to **suppress outside the approved rules, write a system of record, or
  send/submit/file** → refuse; package and route to a human.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Assessment-packaging is deliberately
separated from specialist investigation, incident command, and privacy/legal breach
adjudication (different entitlements, evidence depth, and authority). Upstream, a DLP/SIEM
alert or `security-alert-triage-assistant` (a `data-exfil` route) feeds this skill; it emits a
durable `case_id` + assessment-context bundle + evidence references and advisory routes. It
must not perform the specialist's work, determine a breach, decide a notification, or act.

## Inputs and prerequisites
- A batch-intake object: `config_version`, `template_version`, `batch_id`, `source_queue`,
  `required_approvals[]`, `recorded_approvals[]`, `classification_config{}`, `severity_config{}`,
  `approved_destinations[]`, `approved_fp_patterns[]`, `open_cases[]`, and the `events[]` (each
  with DLP rule, channel, vector, window, source ref, actor, asset, destination, data types +
  counts, egress flag, and signal ids). Schema and field list:
  [scripts/validate_input.py](scripts/validate_input.py).
- Read access to DLP console/SIEM-SOAR, IAM, CMDB, egress proxy, threat intelligence, data
  classification, and incident/BCP systems — all read-only.
- The **approved suppression rule set**, **classification config**, **severity config**, and
  **output template** are versioned config.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The DLP console/SIEM-SOAR is the
system of record for event/case state and the `case_id`; IAM for actor privilege; CMDB for
asset; the egress proxy and threat intelligence for destination trust; the classification
service for data types. **Cite every enriched signal.** An uncited "present" evidence section
is treated as unsupported and fails the output screen. **Never reproduce the data content** —
reference it by classification, type, and count only.

## Workflow
1. **Validate intake** — run [scripts/validate_input.py](scripts/validate_input.py); fail
   closed on structural problems, warn on classification/enrichment gaps (they force
   `needs-data`) and on hard-boundary / suppression-override indicators.
2. **Enrich & classify (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): resolves each
   event's actor/asset/destination, classifies the data by the highest-sensitivity detected
   type, and records citations.
3. **Estimate exposure** — determine egress, destination trust, record/volume magnitude, and
   whether **regulated data left the perimeter** — the key signal for human breach adjudication.
4. **Correlate & deduplicate** — match against open cases on actor+rule+window; **link**, never
   merge or close. A subset match is an exact duplicate; an overlap is a correlated duplicate
   linked for human review.
5. **Score severity (deterministic)** — compute a documented severity from classification,
   egress, destination trust, magnitude, and actor privilege. An `active_exfiltration`
   indicator forces `S1` and a hard boundary.
6. **Apply approved suppression only** — if and only if an event matches an **approved** rule
   (`SUP-DUP-01` exact duplicate, `SUP-SANCTIONED-01` approved sanctioned destination with
   non-regulated data, `SUP-FP-PATTERN-01` documented false-positive pattern), mark
   `approved-suppressed` with the rule id and evidence. Anything else is **not** suppressible; an
   `active_exfiltration` indicator overrides suppression.
7. **Preserve evidence & package** — record evidence references and legal-hold flags for
   chain-of-custody (references only — acquire/alter/remove nothing), and assemble the
   review-ready assessment context (enrichment, classification, exposure, correlation, severity,
   advisory next steps) with citations and a durable `case_id`.
8. **Validate output** — run [scripts/validate_output.py](scripts/validate_output.py); fail
   closed on any control breach. Present the package for human review; do not send it.
9. **Never decide or act** — no breach determination, notification, incident closure,
   containment, or system write.

## Validation loop
Run `validate_input` before and `validate_output` after. The output check enforces: allowed
draft status only; all required template sections present; no unsupported claims (present
evidence sections carry citations); only approved suppression rules; escalated events carry
cited assessment context; severity ties to the deterministic mapping; required approvals
recorded; hard-boundary consistency; and screens for breach-determination/closure,
containment/response, filing/system-write, and send/submit language. Fail closed on any miss.
See [references/controls.md](references/controls.md) and
[references/domain-rules.md](references/domain-rules.md).

## Human approval
`required`. This skill enriches, classifies, estimates exposure, preserves evidence, and
packages; a human privacy/IR owner adjudicates and decides. Every breach determination, every
notification decision, every incident disposition/closure, and every containment or response
action require the authorized human role (DLP/privacy analyst, incident-response reviewer /
privacy officer as configured). Obtaining the recorded approvals is the human step — the draft
merely lists them as pending.

## Failure handling
- **Unresolvable classification/enrichment** (no data types, actor not in IAM, no signal ids)
  → set `needs-data`, list exactly what is missing; do not guess to classify or clear an event.
- **Active-exfiltration indicator** → hard boundary: `package_status=blocked`, urgent route to
  `cyber-incident-response-coordinator` and privacy/legal; perform no containment and make no
  breach determination.
- **Ambiguous correlation/dedup** → link as *correlated-duplicate* for human confirmation; never
  auto-merge or auto-close.
- **Regulated data egress to an untrusted/personal destination** → raise severity and flag for
  human breach adjudication; do not conclude a breach.
- **Stale/conflicting sources** → cite both with dates/versions and flag the conflict; escalate.
- **Tool timeout / partial data** → return a partial package with an explicit incompleteness
  flag and `needs-data`; assume no automatic retry.

## Output contract
1. **Draft incident-assessment package** — the required template sections (batch overview,
   enrichment, data classification, exposure assessment, correlation/dedup, severity, suppression
   log, evidence preservation, escalation routing, approvals, sources, standing note), each
   cited, keyed to [assets/output-template.md](assets/output-template.md).
2. **Package status** — `ready-for-review` | `needs-data` | `blocked` (never a decision).
3. **Per-event disposition** — `prepared-for-review` | `approved-suppressed` | `needs-data` |
   `correlated-duplicate`, with a one-line cited reason.
4. **Assessment-context bundle** (per escalated event) — enrichment, classification, exposure,
   correlation, severity, advisory next steps, citations, durable `case_id`.
5. **Evidence manifest** — per-event source/signal references, integrity reference, legal-hold
   flag, and chain-of-custody note (references only).
6. **Suppression log** — rule id + evidence for each `approved-suppressed` item.
7. **Approval ledger** — every required role with status (pending until a human signs).
8. **Machine-readable** — the package JSON keyed by `case_id`.
9. **Standing note** — draft-only; no breach determination, notification, disposition,
   containment, system write, or send.

## Privacy and records
**Confidential (security-sensitive).** Restrict distribution to the DLP/privacy/IR workflow on a
need-to-know basis. Mask actor identifiers, asset names, and destinations to what the event
evidences (`identity_ref`, `asset_ref`, `dest_ref` are masked); **do not reproduce the
exfiltrated data content** — reference it by classification, type, and count. Preserve
chain-of-custody by recording references and legal-hold flags, never by acquiring or altering
the data. Retain the package, citations, and config/template versions per security-records and
privacy recordkeeping policy; log the analyst identity on every read and every package assembly.

## Gotchas
- **Assessment ≠ breach determination.** Classifying data and estimating exposure informs a
  human breach decision; it never concludes that a reportable breach occurred.
- **Exposure ≠ notification.** "Regulated data left the perimeter" is a signal for privacy/legal;
  the notification obligation is theirs to decide, never this skill's.
- **Suppression ≠ closure.** Approved suppression clears *noise* under a named rule and is
  auditable; regulated data is never suppressed as "approved business use," and an
  `active_exfiltration` indicator overrides suppression.
- **Dedup links, never deletes.** A duplicate points to its parent case; the parent is still worked.
- **Severity is triage, not a verdict.** An `S1` band routes attention; it does not conclude loss.
- **Evidence is preserved by reference.** The skill records references and legal-hold flags; it
  acquires, alters, and removes nothing (no spoliation).
- **Draft-only.** The package is never sent, submitted, filed, or written to the DLP console/case
  system; delivery, notification, and any response action are separate authorized human steps.
