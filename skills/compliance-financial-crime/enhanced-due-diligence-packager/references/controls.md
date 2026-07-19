# Controls — enhanced-due-diligence-packager

- **Risk tier:** R3 — regulated/control decision support. **Action mode:** Draft-only; no
  system-of-record change. The package is a *recommendation with evidence* for a human.
- **Human approval:** `required` — before any onboarding/retention/exit decision, any
  risk-rating change of record, any case closure, and any filing. Assembling the draft is not
  itself an approval.

## Prohibited (fail closed)

- **Onboarding / retention / exit decisions** or any communication of one.
- **Risk-rating changes of record** (the residual-risk band is an indicator only).
- **Case closure**, **SAR/CTR/STR drafting or filing**, or any regulatory submission.
- **Writing a system of record** or **sending/submitting** the package (draft-only).
- **Sanctions-match adjudication**, **UBO verification**, or **adverse-media disposition**
  as a conclusion — route to the specialist.
- **Tipping-off**: any customer-facing content revealing monitoring or SAR activity.

## Packaging states (this skill may set only these)

`blocked` (hard boundary) | `needs-evidence` (any evidence gap) | `ready-for-adjudication`
(complete, no hard boundary). It may **not** set `approved`, `onboarded`, `declined`,
`closed`, `filed`, or any decision/closure state.

## Required output screens (`../scripts/validate_output.py`)

- `packaging_status` is one of the three allowed draft states.
- **Template fidelity:** all fifteen required sections present (see
  [../assets/output-template.md](../assets/output-template.md)).
- **No unsupported claims:** every `present` evidence section carries citations.
- **Required approvals recorded:** the ledger covers every required role; any `obtained`
  entry names an approver **and** date (no fabricated sign-off).
- **Hard-boundary consistency:** a hard boundary / `Prohibited-proximity` band forces
  `blocked`.
- **Language screens:** no decision/closure language (`customer approved`, `case closed`,
  `cleared`, `rating updated in the system`, …); no filing language (`filed the SAR`,
  `submitted to FinCEN`, …); no send/submit language.
- **Standing note present** (draft-only / no-decision limitation).

## Segregation of duties

Packaging entitlements are distinct from adjudication and from any system-of-record write.
The same person/skill must not both assemble the package and adjudicate the relationship or
change the rating of record.

## Data classification, privacy, records

- **Restricted (AML/BSA).** SAR-confidentiality and tipping-off controls apply.
- Mask customer/account identifiers to what the evidence requires (`customer_ref` is masked).
- Retain the package, citations, and config/template versions per BSA recordkeeping; log the
  investigator identity on every read and every package assembly.
