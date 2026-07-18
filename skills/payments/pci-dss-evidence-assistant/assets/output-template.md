# PCI DSS Evidence Package (DRAFT) — {{entity}}

> Draft evidence support only; this package does not attest PCI DSS compliance, does not
> mark any requirement In Place, and is not an AOC, ROC, or SAQ. Every compliance
> determination and attestation is reserved to a QSA, authorized ISA, or the organization's
> authorized signer.

The eight numbered sections below are **required** and are checked by
`scripts/validate_output.py` (template fidelity). `scripts/calculate_or_transform.py` renders
this document from the input; keep the headers verbatim.

## 1. Assessment Scope and Metadata
- Entity: {{entity}}
- PCI DSS version: {{pci_dss_version}}   (pin the exact version, e.g. 4.0.1)
- Assessment type: {{assessment_type}}   (SAQ type or ROC — draft support)
- Assessment period: {{from}} to {{to}}
- As-of date: {{as_of_date}}
- Config version: {{config_version}} (freshness-window + remediation config)

## 2. Cardholder Data Environment (CDE) Summary
- CDE summary: {{cde_summary}}
- Scope note: evidence-readiness support for a QSA/ISA-led assessment; this package does not
  validate scope. No PAN/SAD appears here — pointers and masked identifiers only.

## 3. Requirement-to-Control-to-Evidence Mapping
One row per assessed requirement. `Evidence readiness` is one of `evidence-complete`,
`evidence-gap`, `evidence-stale`, `needs-data`, `not-applicable` — never a determination.

| Requirement | Controls | Evidence readiness | Evidence refs | Reason |
| ----------- | -------- | ------------------ | ------------- | ------ |
| {{req_id}} {{title}} | {{control_ids}} | {{status}} | {{evidence_refs}} | {{reason}} |

## 4. Evidence Readiness Summary
- Total requirements assessed: {{total}}
- evidence-complete / evidence-gap / evidence-stale / needs-data / not-applicable: counts
- NOTE: counts describe evidence readiness only and are NOT a compliance determination.

## 5. Gap and Remediation Register
One row per affected control for each `evidence-gap` / `evidence-stale` requirement.

| Requirement | Control | Issue | Remediation owner | Target date | Severity |
| ----------- | ------- | ----- | ----------------- | ----------- | -------- |
| {{req_id}} | {{control_id}} | {{issue}} | {{owner}} | {{target_date}} | {{severity}} |

## 6. Assumptions and Open Items
- Assumptions and items pending input from the PCI program manager.
- N/A determinations require documented justification per PCI DSS; unjustified N/A ⇒
  needs-data.

## 7. Source and Citation Index
- Per requirement: the `{source_system}:{source_ref}@{effective_date}` citations backing the
  readiness status.

## 8. Approvals and Attestation Boundary
- Prepared by: {{prepared_by}}
- Compliance reviewer: {{compliance_reviewer}} (name or `pending`)
- QSA / authorized ISA sign-off: pending (attestation is NOT performed by this skill)
- Attestation made by this package: NO (`attestation_made: false`)
- Standing note: draft-only; this package does not attest PCI DSS compliance.
