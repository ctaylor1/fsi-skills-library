# Suspicious Activity Report (SAR) — DRAFT Case Package

> Draft-only artifact. This template records a fact-based narrative, source citations, amount
> and chronology tie-outs, a typology assessment, and an advisory review path. It records
> **no determination** and performs **no filing**. The suspicion / file-no-file decision, any
> case closure or disposition, and the filing itself are made by the authorized human (SAR
> quality reviewer / MLRO / BSA Officer) via BSA E-Filing.
>
> Fields in `{{ }}` are populated from the approved investigation case by
> [../scripts/calculate_or_transform.py](../scripts/calculate_or_transform.py). The fourteen
> section headings below are the required template sections enforced by
> [../scripts/validate_output.py](../scripts/validate_output.py) (`REQUIRED_SECTIONS`). Every
> asserted fact must carry a `{system}:{ref}@{date/version}` citation; an uncited fact, a
> tie-out break, an uncovered party, or an unsupported typology is a **gap** and forces
> `packaging_status = needs-evidence`.

- **Case ID:** `{{case_id}}`   **Approving investigation:** `{{approving_investigation}}`
- **Jurisdiction:** `{{jurisdiction}}`   **Template version:** `{{template_version}}`
- **Packaging status:** `{{packaging_status}}`  (`ready-for-quality-review` | `needs-evidence` | `blocked`)

---

## 1. Filing Header  `filing_header`
Case ID, approving investigation, `filing_type` (initial/continuing/corrected), prior SAR
reference, activity-detected date, and regulatory deadline — **context only for the human
filer**. This package sets no filing status of record and does not file.

## 2. Subjects & Parties  `subjects`
Every subject and counterparty (masked names/identifiers), role, type, and relationship.
**Party coverage:** every party referenced by a transaction must appear here; an uncovered
party is a gap.

## 3. Accounts & Instruments  `accounts_instruments`
Accounts (masked) and instruments involved (cash, wire, ACH, etc.).

## 4. Activity Summary  `activity_summary`
Activity period, aggregate amount, currency, transaction count, and the tie-out status.

## 5. Chronology of Activity  `chronology`
Dated, ordered events (`date`, `txn_id`, `amount`, `instrument`, parties) — **each event
cited** to its transaction source. An uncited event is a gap.

## 6. Amount & Chronology Tie-Out  `amount_tie_out`
`status` (`pass` | `break`), `computed_total` vs. `declared_total`, computed vs. declared
period, and computed vs. declared count. A `break` forces `needs-evidence`; a claimed `pass`
must actually reconcile.

## 7. Typology Assessment  `typology_assessment`
Declared typologies mapped to the **approved typology library**: `in_library`, observed vs.
required indicators, `missing_indicators`, and `supported`. An out-of-library or
under-evidenced typology is a gap — not asserted.

## 8. SAR Narrative (5W + How)  `narrative`
`who`, `what`, `when`, `where`, `why`, `how` — a clear, complete, **fact-based** account.
Backed by the evidence index; no speculation or conclusions of guilt. All six elements
required.

## 9. Evidence Index  `evidence_index`
Each asserted fact mapped to a `{system}:{ref}@{date/version}` citation. An uncited fact is a
gap.

## 10. Investigation Rationale  `investigation_rationale`
Why the activity is suspicious, grounded in the approving investigation's findings and cited.
A fact-based rationale — **not a conclusion of guilt**.

## 11. Recommended Review Path  `recommendation`
`recommended_review_path` (advisory): `quality-review-and-compliance-approval` |
`return-for-evidence` | `hold-pending-investigation`. A recommendation, **not a
file/no-file decision**.

## 12. Approvals & Sign-off  `approvals`
`required[]` roles and a `ledger[]` with each role's status (`pending` until a human signs;
an `obtained` entry names the approver **and** date). Obtaining these sign-offs and the
filing decision are the human steps.

## 13. Sources & Citations  `sources_citations`
Aggregate list of every `{system}:{ref}@{date/version}` citation used above.

## 14. Standing Note / Limitations  `standing_note_limitations`
> Draft SAR package for compliance quality review and human filing only. This package records
> fact-based narrative, source citations, tie-outs, and an advisory review path; it makes no
> suspicion or file/no-file determination, files nothing, e-files nothing, submits nothing to
> FinCEN, closes or dispositions no case, writes no system of record, adds no speculation
> beyond the evidence, and has not been sent. Every regulated decision and the filing itself
> remain with the authorized human.
