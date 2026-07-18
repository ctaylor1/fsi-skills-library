# Controls — pci-dss-evidence-assistant

- **Risk tier:** R2 — analytical / drafting support. **Action mode:** Draft-only; no
  system-of-record change.
- **Human approval:** `external-delivery` — human approval required before any external
  delivery (to a QSA, acquirer, or card brand) or any system-of-record change; internal
  drafting is reviewer-sampled.

## Prohibited (fail closed)

- **Attesting compliance** or asserting the entity "is compliant" / "fully compliant".
- **Compliance determinations** — marking any requirement *In Place* / *Not In Place*, or
  declaring a requirement "met" / "satisfied". The skill labels **evidence readiness** only.
- **Signing or submitting** an AOC, ROC, or SAQ, or transmitting the package externally.
- **Scope validation** — confirming CDE scope is a QSA/ISA activity; this skill summarizes
  scope inputs but does not validate them.
- **Fabricating or inferring evidence** — an unmapped requirement is `needs-data`, never
  assumed covered; undatable evidence is treated as stale.

## Evidence-readiness states (this skill may set only these)

`evidence-complete` | `evidence-gap` | `evidence-stale` | `needs-data` | `not-applicable`.
None of these is a compliance determination. It may **not** set `In Place`, `Not In Place`,
`compliant`, `pass`, or `attested`.

## Required output screens (`scripts/validate_output.py`)

- **Template fidelity:** all eight required sections present in the rendered document.
- **No unsupported claims:** every `evidence_ref` exists in the evidence index;
  `evidence-complete` / `evidence-stale` requirements cite evidence; `evidence-gap`
  requirements appear in the gap register.
- **No attestation/determination language** (regex screen: "we are compliant", "fully
  compliant", "marked in place", "requirement is met", "passed the assessment", "AOC
  signed", etc.).
- **Approvals recorded:** `prepared_by`, `compliance_reviewer` (name or `pending`),
  `qsa_or_isa_signoff` slot; `attestation_made` is `false`.
- **Standing note present:** the draft-only / non-attestation statement.

## Segregation of duties

The analyst who assembles the evidence package is distinct from the QSA/authorized ISA who
assesses and attests. This skill prepares and packages; it never performs the assessor's
determination or the authorized signer's attestation.

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII; cardholder data).** Never place PAN/SAD in the
  package; reference tokenized/masked identifiers and evidence pointers only.
- Store only evidence *pointers/citations* and control metadata, not cardholder data.
- Retain the package, its `config_version`, freshness-window version, and citations per the
  organization's PCI evidence-retention policy; log the preparer identity on every build.
