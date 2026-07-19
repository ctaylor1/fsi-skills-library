# Controls — regulatory-exam-response-packager

- **Risk tier:** R3 — regulated/control decision support. **Action mode:** Draft-only; no
  system-of-record change. The package is a draft for human review and human submission.
- **Human approval:** `required` — before any item is treated as ready, and before the package
  is submitted to the regulator, an exam item is closed, or any system of record is written.
  This skill records approvals; it does not grant them.

## Prohibited (fail closed)

- **Submitting / sending / transmitting** the response to the regulator or examiner.
- **Closing or resolving** the examination, inquiry, or any exam item / finding / MRA.
- **Regulated attestation or certification** on the institution's behalf ("we hereby
  certify/attest/represent").
- **Unsupported assertions** presented as ready — any claim without a source citation.
- **Marking an item ready** while a required approver role is not recorded as approved.
- **Writing a system of record** (case state, filing system, records archive).

## Item states (this skill may set only these)

Per request: `gap` → `needs-evidence` → `incomplete` → `unsupported-assertion` →
`needs-approval` → `draft-ready-for-review`. Package readiness is always
`draft-not-submitted`. It may **not** set `submitted`, `filed`, `closed`, or `resolved`.

## Required output screens (`scripts/validate_output.py`)

- All ten template sections present (template fidelity vs. `assets/output-template.md`).
- Only allowed coverage/response_status values; no submission/closure states.
- No unsupported assertion inside any `draft-ready-for-review` item; a ready item is cited.
- Every required approver role recorded as approved before an item is ready.
- `readiness == "draft-not-submitted"`.
- No submission/closure/regulated-decision language (regex: "package has been submitted",
  "sent to the regulator", "examination is closed", "no further action required", "hereby
  certify", …).
- Standing note present: "Draft response package only; not submitted to any regulator, no exam
  item closed, and no system of record updated."

## Segregation of duties

Assembling the package is distinct from approving its contents and from submitting it. The
preparer must not also be the sole approver; submission to the regulator is a separate,
authorized human act. Legal/regulatory-affairs sign-off is required where configured.

## Data classification, privacy, records

- **Restricted (AML/BSA).** SAR-confidentiality and tipping-off controls apply: never expose
  SAR existence or subject-level detail to unauthorized parties, and never draft
  customer-facing text that reveals monitoring or SAR activity. Aggregate/desensitized
  statistics provided to the examining regulator are handled under the confidentiality rules
  and access controls, not disclosed more broadly.
- Mask customer/account identifiers to what the response requires; prefer aggregates.
- Retain the package, its citations, the approver sign-offs, and the template/config version
  per recordkeeping obligations; log preparer identity and every read.
