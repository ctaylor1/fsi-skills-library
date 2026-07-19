# Enhanced Due Diligence (EDD) Package — DRAFT for Adjudication

> Draft-only artifact. This template records evidence, sources, a residual-risk indicator, and
> a recommendation. It records **no decision**. The onboarding/retention/exit decision, any
> risk-rating change of record, and any filing are made by the human adjudicator.
>
> Fields in `{{ }}` are populated from the case intake by
> [../scripts/calculate_or_transform.py](../scripts/calculate_or_transform.py). The fifteen
> section headings below are the required template sections enforced by
> [../scripts/validate_output.py](../scripts/validate_output.py) (`REQUIRED_SECTIONS`). Every
> evidence assertion must carry a `{system}:{ref}@{date/version}` citation; an uncited or
> missing section is a **gap** and forces `packaging_status = needs-evidence`.

- **Case ID:** `{{case_id}}`   **Customer (masked):** `{{customer_ref}}`
- **Jurisdiction:** `{{jurisdiction}}`   **Template version:** `{{template_version}}`
- **Packaging status:** `{{packaging_status}}`  (`ready-for-adjudication` | `needs-evidence` | `blocked`)

---

## 1. Case & Customer Overview  `customer_overview`
Identity verification, customer type, occupation/role. Status: `{{status}}`. Citations required.

## 2. EDD Trigger & Scope  `edd_trigger_scope`
Triggers (`{{triggers}}`), jurisdiction, and the risk rating of record **carried for context
only** — this package does not change it.

## 3. Source of Funds (SoF)  `source_of_funds`
Origin of the specific funds, corroborated by documents. Status + citations.

## 4. Source of Wealth (SoW)  `source_of_wealth`
Origin of overall wealth, independently documented. Status + citations.

## 5. Ownership & Control (UBO)  `ownership_control`
UBO traced; nominee/opacity assessed. Status + citations.

## 6. Geographic Exposure  `geography_exposure`
Residence/funding/business nexus against high-risk (e.g., FATF) lists. Status + citations.

## 7. Adverse Media  `adverse_media`
Search results, severity, and charge/conviction status. Status + citations. Disposition of the
media is the `adverse-media-investigator`'s call — package the evidence and route.

## 8. PEP & Sanctions Screening  `pep_sanctions_screening`
PEP status and sanctions result. A **sanctions true-match is a hard boundary**:
`packaging_status = blocked`, routed to `sanctions-match-adjudicator`. Status + citations.

## 9. Expected Activity & Rationale  `expected_activity`
Expected volumes/patterns, consistent with SoF/SoW. Status + citations.

## 10. Ongoing Monitoring & Controls  `ongoing_monitoring_controls`
Enhanced monitoring plan, review cadence, escalation path. Status + citations.

## 11. Residual Risk Assessment  `residual_risk_assessment`
`residual_risk_band` (Low/Medium/High/Prohibited-proximity), `score`, and the documented
`factors`. **Indicator only — not a rating of record.**

## 12. Recommendation for Adjudication  `recommendation`
`recommended_review_path` (advisory) + rationale. A recommendation, **not a decision**.

## 13. Approvals & Sign-off  `approvals`
`required[]` roles and a `ledger[]` with each role's status (`pending` until a human signs; an
`obtained` entry names the approver and date). Obtaining these approvals is the human step.

## 14. Sources & Citations  `sources_citations`
Aggregate list of every `{system}:{ref}@{date/version}` citation used above.

## 15. Standing Note / Limitations  `standing_note_limitations`
> Draft EDD package for human adjudication only. This package records evidence, source
> citations, and a risk-based recommendation; it makes no onboarding, retention, exit, or
> risk-rating decision, files no report, writes no system of record, and has not been sent or
> submitted. Every regulated decision and filing remains with the authorized adjudicator.
