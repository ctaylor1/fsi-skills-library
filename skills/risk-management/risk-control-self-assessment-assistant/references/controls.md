# Controls — risk-control-self-assessment-assistant

- **Risk tier:** R3 — regulated/control decision support. **Action mode:** Draft-only; no
  system-of-record change. The package is a **draft** for human adjudication.
- **Human approval:** `required` — control/process owner attestation, first-line management
  sign-off, and **independent second-line challenge/validation** before the RCSA is a record.
- **Three-lines separation:** this skill is first-line drafting support. It must not stand in
  for the second-line independent challenge, and the same person must not both draft and
  provide the independent challenge.

## Prohibited (fail closed)

- **Sign-off, attestation, self-certification, closure, or finalization** of an RCSA.
- Making or recording a **risk-acceptance** decision, or setting residual/appetite outcomes
  as binding.
- **Writing the GRC system of record** or otherwise treating the draft as filed.
- **Crediting a control without evidence** (any Effective / Partially Effective conclusion
  must carry evidence, else it is Unsubstantiated).
- **Closing or waiving remediation**, or asserting "no remediation required" as a decision.

## Draft states (this skill produces only these)

A package is always **DRAFT**. Per risk it reports one residual band and a
`remediation_required` flag; per control an effectiveness conclusion (including
`Unsubstantiated`). It may **not** produce `approved`, `attested`, `signed-off`, `closed`,
`finalized`, or `risk-accepted` states — those belong to the humans in §Human approval.

## Required output screens (`scripts/validate_output.py`)

- All required template sections present (assessment_scope, risk_and_control_assessment,
  residual_risk_summary, evidence_map, challenges_and_gaps, remediation_plan, approvals).
- **No unsupported assertions:** any credited (Effective / Partially Effective) control
  effectiveness carries evidence.
- **Residual tie-out:** `residual_level == max(1, inherent_level − control_effect_reduction)`
  and the band matches the level table.
- **Ineffective control triggers remediation:** any control rated `Ineffective` must have
  `remediation_required` set (checked independently so a masked Ineffective fails closed).
- **Required approvals recorded:** the three approval roles are present; none is marked
  `obtained` without a named approver and date (the assistant emits `pending`).
- **No autonomous-decision language:** no sign-off/attestation/closure/filing/risk-acceptance
  phrasing (regex screen).
- Standing note present.

## Human approval (who decides)

| Decision | Owner |
| -------- | ----- |
| Accuracy of risk/control statements & ratings | Control / process owner (first line) |
| Assessment sign-off | First-line business management |
| Independent challenge & validation | Second-line operational risk |
| Remediation acceptance, waiver, or risk acceptance | Accountable risk owner / risk committee per appetite |
| Writing the RCSA to the GRC system of record | Human via GRC platform (approval broker) |

## Data classification, privacy, records

- **Confidential.** Mask personal identifiers; RCSA content is internal control information.
- Retain the draft, its evidence citations, and the methodology/appetite versions with the
  final GRC record per records-retention policy; log the preparer identity and every source
  read. The draft itself is not a record until human sign-off is captured in the GRC system.
