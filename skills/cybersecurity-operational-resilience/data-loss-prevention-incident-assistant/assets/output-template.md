# DLP Incident Assessment Package — DRAFT for Privacy/IR Review

> Draft-only artifact. This template records event enrichment, a deterministic data
> classification, an exposure estimate, correlation, a documented severity, an
> approved-suppression log, evidence references for chain-of-custody, and review-ready
> assessment context. It records **no decision**. Any breach determination, incident
> disposition/closure, notification obligation, containment (blocking/quarantine/revocation/
> deletion/recall), account disable, system-of-record write (DLP console / case management /
> ticketing), or delivery is performed by the human privacy/incident-response owner and
> legal/compliance.
>
> Fields in `{{ }}` are populated from the event batch by
> [../scripts/calculate_or_transform.py](../scripts/calculate_or_transform.py). The section
> keys below are the required template sections enforced by
> [../scripts/validate_output.py](../scripts/validate_output.py) (`REQUIRED_SECTIONS`). Every
> enriched signal must carry a `{system}:{ref}@{date/version}` citation; an uncited "present"
> evidence section is an unsupported claim and fails the output screen.

- **Batch ID:** `{{batch_id}}`   **Source queue:** `{{source_queue}}`
- **Config version:** `{{config_version}}`   **Template version:** `{{template_version}}`
- **Package status:** `{{package_status}}`  (`ready-for-review` | `needs-data` | `blocked`)

---

## 1. Incident Batch Overview  `incident_batch_overview`
Batch id, source queue, total events, disposition counts, and config/template versions. The
`package_status` is a draft state — never a decision, closure, or breach-determination state.

## 2. Event Enrichment  `event_enrichment`
Per-event enrichment from IAM (actor, privilege), CMDB (asset, managed state), and web/mail/
egress proxy (destination, trust, category), plus channel and vector. Status `present`/`empty`;
**citations required** when present.

## 3. Data Classification  `data_classification`
Deterministic classification of the data involved per event (`Restricted (PCI/CHD)` /
`Restricted (PHI)` / `Restricted (PII/NPI)` / `Confidential (IP/Proprietary)` / `Internal` /
`Public`), driven by the highest-sensitivity detected data type. A **recommendation** for human
confirmation, not a legal determination. Status + **citations required** when present.

## 4. Exposure Assessment  `exposure_assessment`
Whether egress completed, destination trust, record/volume magnitude, and whether **regulated
data left the perimeter** — the key signal for human breach adjudication. It is an estimate, not
a breach finding. Status + **citations required** when present.

## 5. Correlation & Deduplication  `correlation_deduplication`
Exact-duplicate and correlated-duplicate links to open cases. Duplicates are **linked** to a
parent case; they are never merged and never dispositioned by this skill.

## 6. Severity Prioritization  `severity_prioritization`
Deterministic, documented severity score, band (`S1 (Critical)` / `S2 (High)` /
`S3 (Moderate)`), and the contributing factors per event. A triage **rank for a human**, not a
verdict. An `active_exfiltration` indicator forces `S1` and a hard boundary.

## 7. Approved Suppression Log  `suppression_log`
Each `approved-suppressed` event with its rule id (`SUP-DUP-01` exact duplicate,
`SUP-SANCTIONED-01` approved sanctioned destination with non-regulated data, `SUP-FP-PATTERN-01`
documented false-positive pattern), evidence, and rule-set version. **No other suppression is
permitted.** Suppression removes known-benign or approved-business noise; it never clears a
genuine incident, and an `active_exfiltration` indicator overrides it.

## 8. Evidence Preservation & Chain-of-Custody  `evidence_preservation`
Per-event evidence references (source ref, signal ids, integrity reference) and legal-hold flags
recorded for the human owner. This skill **records references only** — it acquires, alters, and
removes nothing. Status + **citations required** when present.

## 9. Escalation Routing (advisory)  `escalation_routing`
Advisory handoffs to the appropriate specialist skill or the privacy/incident-response owner.
The human decides and initiates; **no route is executed here.**

## 10. Approvals & Sign-off  `approvals`
`required[]` roles and a `ledger[]` with each role's status (`pending` until a human signs; an
`obtained` entry names the approver and date). Obtaining these approvals is the human step.

## 11. Sources & Citations  `sources_citations`
Aggregate list of every `{system}:{ref}@{date/version}` citation used above.

## 12. Standing Note / Limitations  `standing_note_limitations`
> Draft data-loss-prevention incident assessment for privacy/IR review and human adjudication
> only. This assessment enriches, classifies, estimates exposure, records evidence references,
> and applies only approved suppression rules to raise review-ready context; it makes no breach
> determination, does not confirm or disposition exfiltration, decides no notification
> obligation, blocks/quarantines/revokes nothing, removes or recalls no data, disables no
> account, writes no system of record, and has not been sent, submitted, or filed. Every
> regulated data-loss decision, breach determination, notification, and response action remains
> with the authorized privacy/incident-response owner and legal/compliance.
