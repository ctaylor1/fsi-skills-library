# Controls — regulatory-change-impact-analyzer

- **Risk tier:** R3 — regulated / control decision support. **Action mode:** Read-only analysis.
- **Human approval:** `required` — a human must adjudicate applicability, disposition, and
  closure before any regulated decision, filing, commitment, posting, or system-of-record
  change. The skill produces evidence and a recommendation only.

## Prohibited (fail closed)

- No **compliance determination** — never state or imply the firm **is** (or is not)
  compliant, that an obligation is satisfied, or that a gap does/does not create a violation.
- No **applicability decision that closes scope** — recommend applicability with evidence; a
  human confirms in-/out-of-scope and any exemption.
- No **change/item closure**, disposition sign-off, or suppression of an obligation.
- No **filing, submission, or attestation** to a regulator, and no certification of
  compliance.
- No **system-of-record write** (change register, policy, control, GRC record).
- No **conflict resolution** — surface conflicting requirements across instruments or
  jurisdictions and route to legal/compliance; do not pick a winner.
- No **legal advice** — obtain a legal reading for interpretation questions.

## Required output screens (`scripts/validate_output.py`)

- Every raised finding has ≥1 cited evidence row.
- `recommended_disposition` equals the deterministic mapping from `raised_findings`.
- No prohibited decision / closure / filing / attestation language (regex screen: "the firm
  is compliant", "no further action required", "closing this change", "certify compliance",
  "file the report", "sign-off", etc.).
- Standing disclaimer present (impact/evidence only; adjudication required; no decision/filing
  made).
- `mandatory_adjudication` is `true`.
- `open_questions` (adjudication prompts) included whenever any obligation is applicable.

A **non-compliant fixture** (`evals/files/change_with_decision.json`) exercises this screen
and must exit non-zero (fail closed).

## Data classification, privacy, records

- **Restricted.** Instrument text is public; firm business lines, inventory, owners, and
  implementation notes are internal. Minimize internal data to what evidences a finding.
- Retain the assessment + citations + config version per records policy; log the read and
  the human adjudication decision. Do not exfiltrate the inventory or owner data.

## Reproducibility

`assessment_id` binds the output to the exact instrument, obligations, firm profile,
inventory snapshot, and **config version**; re-running with the same inputs reproduces the
findings and disposition. Disposition is a **triage recommendation for a human adjudicator**,
never an autonomous decision.
