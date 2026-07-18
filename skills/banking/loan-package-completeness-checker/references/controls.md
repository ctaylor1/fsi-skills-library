# Controls — loan-package-completeness-checker

- **Risk tier:** R3 — regulated/control decision support. **Action mode:** Read-only analysis.
- **Human approval:** `required` — a qualified human certifier must review the assessment and
  make any certification, clear-to-close, condition-waiver, or system-of-record decision.

## Prohibited (fail closed)

- No **credit decision** — never approve or deny a loan, application, or credit, and never
  issue or imply an **adverse action**.
- No **clear-to-close, certification, closing, funding, or booking** of the loan.
- No **condition waiver** or clearing of an outstanding condition — flag it; the human decides.
- No **system-of-record write** or **filing** (HMDA, investor delivery, etc.).
- No **checklist tuning to the individual file**; use only the versioned product/jurisdiction
  checklist and its validity windows and severity mapping.
- No **opaque scoring** presented as decisive; findings are explainable and each is evidenced.

## Required output screens (`scripts/validate_output.py`)

- Every finding has >= 1 cited evidence reference (document / checklist item / condition).
- `counts` equal the recomputed severity tally; `readiness_disposition` equals the
  deterministic mapping from `counts` (see `references/domain-rules.md`).
- No lending-decision / closure / filing / condition-waiver language anywhere in the
  narrative, notes, finding summaries, or certifier actions (regex screen: "clear to close",
  "the loan is approved", "approve the loan", "adverse action", "certify the package",
  "fund the loan", "conditions are waived", "underwriting decision", "file the HMDA", etc.).
- Standing disclaimer present: "Completeness findings and cited evidence only; this is not a
  lending decision or package certification, and no loan action has been taken. Human review
  and certification are required before the package proceeds."
- `certifier_actions` present whenever the package is not Complete (guards **false negatives** —
  every blocker/exception must be surfaced for the human, never silently dropped).

## Readiness disposition (deterministic)

| Disposition | Rule |
| ----------- | ---- |
| **Not-ready (blockers present)** | >= 1 Blocker finding |
| **Conditional (exceptions to adjudicate)** | 0 Blockers, >= 1 Exception |
| **Complete (ready for human certification)** | 0 Blockers and 0 Exceptions (Advisories allowed) |

The disposition is a **completeness recommendation for a human**. It is not a lending
decision and it never certifies, closes, or funds the loan.

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII).** Mask account/loan numbers to last 4 where shown.
- Minimize customer data to what evidences a finding; do not echo full income/asset documents.
- Retain the assessment + citations + `checklist_version` per records policy; log the read and
  the human certification event.

## Reproducibility

`assessment_id` binds the output to the exact package inputs, `as_of`, and the
`checklist_version` / `config_version`; re-running with the same inputs and checklist
reproduces the findings, counts, and readiness disposition.
