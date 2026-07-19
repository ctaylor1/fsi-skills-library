# Controls — model-risk-documenter

- **Risk tier:** R3 — regulated / control decision support. Evidence + recommendations with
  **mandatory human adjudication**. **Action mode:** Draft-only; no system-of-record change.
- **Human approval:** `required` — every section status, finding, recorded approval, and the
  documentation-complete / model-validated determination is reviewed and adjudicated by the
  model owner, independent validation, and the routed approver before any decision. Internal
  drafting may be reviewer-sampled.

## Prohibited (fail closed)

- **Validating, approving, attesting, certifying, or clearing** the model for use or
  deployment. The pack is a draft with a `pending` attestation block; a human decides.
- **Final / binding determination** that the model is validated or its documentation complete.
- **Closing, resolving, or waiving a finding**, or setting a finding to anything but `open`.
- **False attestation** — recording an approval with no cited reference, or marking a section
  `documented` without a versioned source artifact.
- **Fabricated or assumed evidence / versions.**
- **Personalized legal, investment, or compliance advice.**

## Pack / finding / attestation states (this skill may set only these)

Pack: `draft-pack` (all sections have content) | `needs-data` (a section is missing content).
Readiness: `documentation-gaps` | `outstanding-findings` | `draft-complete-pending-review`.
Findings: `open` only. Attestation: `pending` only. It may **not** set `validated`, `approved`,
`certified`, `attested`, `accepted`, `closed`, `resolved`, `waived`, or `cleared`.

## Required output screens (`scripts/validate_output.py`)

- **Template fidelity:** all ten required sections present — `purpose`, `methodology`, `data`,
  `performance`, `limitations`, `controls`, `monitoring`, `changes`, `approvals`,
  `traceability`.
- **Source-to-document traceability:** every `documented` section carries a versioned citation;
  each section's declared status equals the deterministic re-derivation from its evidence and
  required coverage (methodology & limitations coverage recomputed).
- **Finding discipline:** every finding is `open`, sourced, and has a recommended remediation;
  every `gap`/`needs-data` section carries an open documentation finding.
- **No false attestation / consistency:** every recorded approval carries a citation;
  `attestation.status == pending` with `adjudication_required` true and non-empty routing; an
  unconditional `approved` decision cannot coexist with an open High-severity finding.
- **No autonomous-decision language** (regex): `model is validated`, `validation complete`,
  `approved for production/use`, `fit for use/purpose`, `we certify/attest`, `certified`,
  `cleared to deploy`, `sign-off complete`, `no further human review required`, `ready for
  production`, `risk accepted`, `final approval/determination`, plus finding-closure phrases
  (`finding closed/resolved/waived`, `no action required`).
- Standing note present: the draft-only / no-validation / no-approval / no-attestation
  disclaimer.

## Segregation of duties

Documentation assembly is distinct from independent validation, from maintaining the inventory
record, and from the approval / attestation decision. The same person/skill must not both
assemble the pack and validate or approve the model it documents.

## Data classification, privacy, records

- **Confidential.** The pack describes a model and its controls; reference model/data assets by
  catalog ID and cite evidence rather than copying sensitive datasets or customer NPI/PII into
  the pack. Customer data stays in the owning system's controls.
- Retain the draft pack, `template_version` / `framework_version`, citations, and reviewer
  sign-off with the model record; log every read and every pack produced with the reviewer
  identity, per model-risk recordkeeping.
