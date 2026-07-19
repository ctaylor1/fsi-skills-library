# Operational Resilience Report — DRAFT

> **DRAFT - for human review and adjudication; not filed or submitted to any regulator.**

| Field | Value |
| ----- | ----- |
| Report type | `{{report_type}}` |
| Jurisdiction | `{{jurisdiction}}` |
| Template version | `{{template_version}}` |
| Ruleset version | `{{ruleset_version}}` |
| As of | `{{as_of_date}}` |
| Reporting period | `{{reporting_period.from}}` → `{{reporting_period.to}}` |

The section set below is defined by the `report_type` base template plus the `jurisdiction`
pack (versioned contract). Every required section must appear. Each section is either
**drafted** (evidence-cited facts) or a **gap** (no evidence in the dataset; requires human
input). Gaps must not be filled with unsupported content.

---

## {{section.title}}
*Status:* `drafted` | `gap`

- {{content_fact}}  *(each drafted fact carries at least one citation)*

*Citations:* `{{system}}:{{ref}}@{{date|version}}`, …

*(repeat for every required section: executive-summary, important-business-services,
impact-tolerance-statements, mapping-and-third-parties, scenario-testing-summary,
incident-experience / incident-chronology, impact-tolerance-assessment / tolerance-outcomes,
root-cause-and-remediation, customer-and-market-impact, vulnerabilities-and-remediation,
remediation-plan, lessons-learned, concentration-and-substitutability, exit-and-contingency,
critical-third-parties, service-dependency-map, regulatory-notification-status,
board-attestation-status, and any jurisdiction-pack sections — ict-third-party-register,
major-incident-classification, self-assessment-document-reference,
interconnection-and-concentration — as applicable)*

---

## Impact-tolerance assessments (deterministic tie-out)

| Incident | Service | Metric | Threshold | Observed | Direction | Breached | Citation |
| -------- | ------- | ------ | --------- | -------- | --------- | -------- | -------- |
| INC-… | IBS-… | disruption_minutes | 120 | 205 | max | true | incidents:INC-…@date |

*Breach is a factual observation (observed vs threshold), not a compliance determination.*

## Register completeness

- Critical services: `{{n}}` · Important business services: `{{n}}` · Critical third parties: `{{n}}`
- Missing required fields: `{{list, empty if complete}}`

## Gaps / needs human input

- `{{section}}: {{note}}` *(each unresolved section, with what is required)*

## Approvals (recorded — human)

| Role | Name | Decision | Date |
| ---- | ---- | -------- | ---- |
| accountable-executive | … | approved | yyyy-mm-dd |
| second-line-review | … | approved | yyyy-mm-dd |

*Both required approvals must be recorded and `approved` before the draft is
review-complete. These decisions are made by humans and recorded here; the skill does not
grant them.*

---

**Standing note:** Draft resilience report only; this package makes no regulatory
determination, files nothing, and submits nothing. A named accountable executive and
second-line reviewer must adjudicate, and any regulatory submission is performed by an
authorized human.
