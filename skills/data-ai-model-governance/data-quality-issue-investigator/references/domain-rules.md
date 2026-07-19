# Domain Rules — data-quality-issue-investigator

Orientation references: BCBS 239 (risk data aggregation and quality), DAMA-DMBOK data-quality
dimensions, and SR 11-7 / model-risk expectations for data feeding models. The firm's data
governance standard and its **severity config** take precedence and are versioned contracts.

## Data-quality dimensions (defect_type)

`completeness`, `validity`, `uniqueness`, `consistency`, `timeliness`, `accuracy`. A missing
or unrecognized `defect_type` forces `needs-data` — the defect cannot be profiled by guessing.

## Severity scoring (deterministic, documented)

Severity is computed from explainable inputs; the mapping is configuration, not judgment.

| Input | Contribution (default) |
| ----- | ---------------------- |
| Failure rate (failing/total) | ≥ 0.20 +3, ≥ 0.05 +2, ≥ 0.01 +1 |
| Feeds a regulatory report | +4 (also forces Critical band) |
| Feeds a material model (materiality High/Critical) | +3 |
| Feeds a regulated decision | +3 |
| Data classification | Restricted +2, Confidential +1, Internal/Public 0 |
| Distinct downstream consumers | +1 each, capped +3 |
| Recurrence (prior issues on this dataset in 90d) | +1 per prior, capped +2 |

Bands (default thresholds `s1_min` 9, `s2_min` 5, `s3_min` 2): **S1 (Critical)** total ≥ 9
**or** any regulatory-report consumer; **S2 (High)** 5–8; **S3 (Moderate)** 2–4; **S4 (Low)**
≤ 1. The thresholds are part of the versioned `severity_config`; a deployment may override
them, and the engine records the config it used on the output so the band is reproducible and
ties out. Severity is a recommended rank for a human owner, not a final determination.

## Disposition routing (recommendation only)

| Disposition | Condition | Route |
| ----------- | --------- | ----- |
| `recommend-incident-escalation` | Feeds a regulatory report, a material model, or a regulated decision, **or** band is S1 | `ai-incident-investigator` |
| `recommend-upstream-trace` | `upstream_suspected` and not material | `data-lineage-documenter` |
| `recommend-remediation` | Substantiated defect, not material, not upstream-suspected | Data owner (human) |
| `possible-duplicate` | Overlaps an open case (same dataset+rule+period, shared record keys) | Link to parent; human confirms |
| `needs-data` | Missing defect type or counts | None — return the gap |

## Hard boundaries (fail closed)

- No **case closure / resolution**, **root-cause confirmation**, **remediated** marking,
  **waiver**, or **filing**.
- No **autonomous final determination** — severity and disposition are recommendations.
- No **auto-merge** of issues/cases; dedup **links** for human confirmation.
- No **down-ranking** of a material/regulated-impact defect below incident escalation.

## Evidence bundle — required contents

Durable `case_id`; defect profile (dataset, field, rule, defect type, period); amounts
(total/failing records, failure rate, affected report/model/decision counts, monetary
exposure); consumers; chronology of timestamped events with citations; parties (data owner,
steward, upstream owner); citations for every item; recommended severity band.
