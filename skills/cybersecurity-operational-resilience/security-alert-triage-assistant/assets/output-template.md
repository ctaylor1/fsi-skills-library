# Security-Alert Triage Package — DRAFT for Analyst Investigation

> Draft-only artifact. This template records enrichment, an affected-asset/identity map,
> correlation, a documented priority, an approved-suppression log, and analyst-ready
> investigation context. It records **no decision**. Any alert closure, incident declaration,
> containment/isolation/blocking/disabling, remediation, system-of-record write (SIEM/SOAR/
> ticketing), or delivery is performed by the human analyst and the incident-response process.
>
> Fields in `{{ }}` are populated from the alert batch by
> [../scripts/calculate_or_transform.py](../scripts/calculate_or_transform.py). The eleven
> section keys below are the required template sections enforced by
> [../scripts/validate_output.py](../scripts/validate_output.py) (`REQUIRED_SECTIONS`). Every
> enriched signal must carry a `{system}:{ref}@{date/version}` citation; an uncited "present"
> evidence section is an unsupported claim and fails the output screen.

- **Batch ID:** `{{batch_id}}`   **Source queue:** `{{source_queue}}`
- **Config version:** `{{config_version}}`   **Template version:** `{{template_version}}`
- **Package status:** `{{package_status}}`  (`ready-for-analyst` | `needs-data` | `blocked`)

---

## 1. Triage Batch Overview  `triage_batch_overview`
Batch id, source queue, total alerts, disposition counts, and config/template versions. The
`package_status` is a draft state — never a decision or closure state.

## 2. Alert Enrichment  `alert_enrichment`
Per-alert enrichment from CMDB (asset), IAM (identity), threat intelligence (severity, IOCs),
and vulnerability/cloud posture (KEV nexus, exposure). Status `present`/`empty`; **citations
required** when present.

## 3. Affected Assets & Identities  `asset_identity_map`
The assets and identities implicated across the batch, with criticality/privilege and the
alerts that reference each. Status + citations.

## 4. Correlation & Deduplication  `correlation_deduplication`
Exact-duplicate and correlated-duplicate links to open cases. Duplicates are **linked** to a
parent case; they are never merged and never dispositioned by this skill.

## 5. Prioritization  `prioritization`
Deterministic, documented priority score, band (`P1 (Critical)` / `P2 (High)` /
`P3 (Moderate)`), and the contributing factors per alert. A triage **rank for a human**, not a
verdict. `known_malicious` threat intel forces `P1`.

## 6. Approved Suppression Log  `suppression_log`
Each `approved-suppressed` alert with its rule id (`SUP-DUP-01` exact duplicate,
`SUP-SCANNER-01` authorized scanner source, `SUP-MAINT-01` documented maintenance window),
evidence, and rule-set version. **No other suppression is permitted.** Suppression removes
known-benign noise; it never clears a genuine alert.

## 7. Analyst-Ready Investigation Context  `investigation_context`
For each `prepared-for-investigation` alert: the enriched asset/identity, signature, window,
signals, threat-intel and posture context, correlated cases, recommended priority, and
**advisory** next steps. Status + citations. Next steps are recommendations only.

## 8. Recommended Routing (advisory)  `recommended_routing`
Advisory handoffs to the appropriate specialist skill or the incident-response process. The
analyst decides and initiates; **no route is executed here.**

## 9. Approvals & Sign-off  `approvals`
`required[]` roles and a `ledger[]` with each role's status (`pending` until a human signs; an
`obtained` entry names the approver and date). Obtaining these approvals is the human step.

## 10. Sources & Citations  `sources_citations`
Aggregate list of every `{system}:{ref}@{date/version}` citation used above.

## 11. Standing Note / Limitations  `standing_note_limitations`
> Draft security-alert triage package for analyst investigation only. This package enriches,
> prioritizes, correlates, and applies only approved suppression rules to raise analyst-ready
> context; it makes no alert-closure, incident, containment, or remediation decision,
> isolates/blocks/disables nothing, writes no system of record (SIEM/SOAR/ticketing), and has
> not been sent or submitted. Every regulated security decision and response action remains
> with the authorized human analyst and incident-response process.
