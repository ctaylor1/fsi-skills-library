# Controls — audit-evidence-packager

- **Risk tier:** R2 — analytical / drafting support. **Action mode:** Draft-only; no
  system-of-record change.
- **Human approval:** `external-delivery` — human approval required before any external delivery
  (to the auditor, regulator, or committee) or any system-of-record change; internal drafting is
  reviewer-sampled.

## Prohibited (fail closed)

- **Concluding on control operating effectiveness** or asserting a control "is effective" /
  "operating effectively". The skill labels **packaging readiness** only.
- **Issuing or implying an audit opinion** (qualified/unqualified) or stating "no exceptions
  noted" / "tested: pass".
- **Signing or providing a management representation / attestation**, or **delivering / submitting**
  the package to the auditor or regulator.
- **Fabricating or inferring evidence** — an unmapped request is `needs-data`, never assumed
  covered; a missing artifact is `evidence-gap`; undatable/out-of-period is `evidence-stale`.
- **Leaking or over-redacting** — raw PII/NPI must be redacted before packaging; redaction must
  not be used to obscure or withhold an otherwise responsive artifact.

## Packaging-readiness states (this skill may set only these)

`packaged-complete` | `evidence-gap` | `evidence-stale` | `redaction-required` | `custody-gap` |
`needs-data` | `not-applicable`. None of these is a control conclusion. It may **not** set
`effective`, `ineffective`, `pass`, `fail`, `no-exceptions`, or `attested`.

## Required output screens (`scripts/validate_output.py`)

- **Template fidelity:** all eight required sections present in the rendered document.
- **Completeness / no unsupported claims:** every `evidence_ref` exists in the evidence index;
  `packaged-complete` requests cite evidence **and** every cited artifact has a complete chain of
  custody; open items (`evidence-gap` / `evidence-stale` / `redaction-required` / `custody-gap`)
  appear in the open register.
- **Redaction integrity:** no `packaged-complete` request carries unresolved redaction.
- **No conclusion/opinion/attestation/delivery language** (regex screen: "controls are operating
  effectively", "no exceptions noted", "we hereby conclude", "audit opinion", "management
  representation is signed", "delivered to the auditor", etc.).
- **Approvals recorded:** `prepared_by`, `control_owner_review` (name or `pending`),
  `audit_coordinator_signoff` slot; `delivered_to_auditor` and `management_assertion_made` are
  `false`.
- **Standing note present:** the draft-only / non-conclusion statement.

## Segregation of duties

The preparer who assembles the evidence package is distinct from the control owner who reviews it,
the audit coordinator who authorizes delivery, and the auditor who tests and concludes. This skill
prepares and packages; it never performs the auditor's testing/conclusion or the signer's
attestation.

## Data classification, privacy, records

- **Confidential (financial records); sampled artifacts may contain employee/customer PII/NPI.**
  Never place raw sensitive values in the package; flag them in `sensitive_fields`, enforce
  redaction, and reference masked identifiers and evidence pointers only.
- Preserve chain of custody (source, preparer, extraction timestamp, checksum); redaction is
  logged and never alters the source of record.
- Retain the package, its `config_version`, custody log, and citations per the organization's
  audit-evidence retention policy; log the preparer identity on every build and any
  external-delivery approval.
