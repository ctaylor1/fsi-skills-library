# Privacy / Data-Protection Impact Assessment (PIA/DPIA) — DRAFT for Sign-off

> Draft-only artifact. This template records the processing, personal-data inventory, legal
> basis, sharing, retention, security, data-subject rights, risks, and mitigations with source
> citations, a privacy-risk indicator, and a recommendation. It records **no decision**. The
> approval of the processing, any lawful-basis of record, any prior consultation with the
> supervisory authority, and any filing are made by the human adjudicator (DPO / privacy
> officer / legal).
>
> Fields in `{{ }}` are populated from the assessment intake by
> [../scripts/calculate_or_transform.py](../scripts/calculate_or_transform.py). The fourteen
> section headings below are the required template sections enforced by
> [../scripts/validate_output.py](../scripts/validate_output.py) (`REQUIRED_SECTIONS`). Every
> evidence assertion must carry a `{system}:{ref}@{date/version}` citation; an uncited or
> missing section is a **gap** and forces `packaging_status = needs-information`.

- **Assessment ID:** `{{assessment_id}}`   **Processing (masked ref):** `{{processing_ref}}`
- **Jurisdiction:** `{{jurisdiction}}`   **Template version:** `{{template_version}}`
- **Packaging status:** `{{packaging_status}}`  (`ready-for-adjudication` | `needs-information` | `blocked`)

---

## 1. Assessment Scope & Trigger  `assessment_scope`
Processing name, the DPIA trigger(s) (`{{triggers}}`), jurisdiction, and the business owner —
carried **for context only**. This assessment does not authorize the processing.

## 2. Processing Description & Purpose  `processing_purpose`
What the processing does, the controller/processor roles, and the specified purpose(s). Status:
`{{status}}`. Citations required.

## 3. Personal Data Inventory & Categories  `data_inventory`
Categories of personal data, any special-category (Art 9) / criminal-offence (Art 10) data,
the data subjects, and volume/scale. Status + citations.

## 4. Legal Basis, Necessity & Proportionality  `legal_basis`
The lawful basis (and any Art 9 condition), the necessity/proportionality assessment, and data
minimization. **No lawful basis, or special-category data with no Art 9 condition, is a hard
boundary** → `blocked`. Status + citations.

## 5. Data Sharing, Recipients & International Transfers  `data_sharing`
Recipients and processors, onward sharing, and any international transfer with its transfer
mechanism. **A restricted transfer with no valid mechanism is a hard boundary** → `blocked`.
Status + citations.

## 6. Retention & Data Minimization  `retention`
Retention periods, deletion routines, and pseudonymization/minimization against the
records-retention schedule. Status + citations.

## 7. Security & Technical/Organizational Measures  `security`
Encryption, access control, logging, vendor assurance, and other technical/organizational
measures protecting the data. Status + citations.

## 8. Data Subject Rights & Transparency  `data_subject_rights`
Transparency/notice, and how access, rectification, erasure, objection/opt-out, and rights
around automated decision-making are supported operationally. Status + citations.

## 9. Risk Mitigations & Safeguards  `mitigations`
The safeguards that reduce the identified risks to data subjects (access restriction, human
review, bias/fairness evaluation, opt-out enforcement). Status + citations.

## 10. Privacy Risk Assessment  `privacy_risk_assessment`
`residual_risk_band` (Low/Medium/High/Unlawful-processing-proximity), `score`, and the
documented `factors` (risk to the rights and freedoms of data subjects). A
`prior_consultation_indicated` flag is advisory. **Indicator only — not a decision on the
processing or a lawful basis of record.**

## 11. Recommendation for Sign-off  `recommendation`
`recommended_review_path` (advisory) + rationale. A recommendation, **not a decision**.

## 12. Approvals & Sign-off  `approvals`
`required[]` roles and a `ledger[]` with each role's status (`pending` until a human signs; an
`obtained` entry names the approver and date). Obtaining these approvals is the human step.

## 13. Sources & Citations  `sources_citations`
Aggregate list of every `{system}:{ref}@{date/version}` citation used above.

## 14. Standing Note / Limitations  `standing_note_limitations`
> Draft privacy impact assessment for human sign-off only. This assessment records evidence,
> source citations, a privacy-risk indicator, and a risk-based recommendation; it makes no
> approval of the processing, sets no lawful basis of record, files nothing with a supervisory
> authority, writes no system of record, and has not been sent or submitted. Every regulated
> privacy decision and sign-off remains with the authorized Data Protection Officer / privacy
> adjudicator.
