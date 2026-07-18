# Audit Evidence Package (DRAFT) — {{entity}}

> Draft evidence support only; this package does not conclude on control operating
> effectiveness, does not issue or imply an audit opinion, and is not a management
> representation. Every testing conclusion, opinion, and attestation is reserved to the
> auditor, control owner, or authorized signer, and delivery to the auditor is a separate,
> human-authorized action.

The eight numbered sections below are **required** and are checked by
`scripts/validate_output.py` (template fidelity). `scripts/calculate_or_transform.py` renders
this document from the input; keep the headers verbatim.

## 1. Audit Engagement Scope and Metadata
- Entity: {{entity}}
- Engagement: {{engagement_name}} ({{engagement_type}})
- Framework/standard: {{framework}}   (e.g., COSO 2013 / SOX 404, PCAOB, internal audit plan)
- Audit period: {{from}} to {{to}}
- As-of date: {{as_of_date}}
- Config version: {{config_version}} (remediation config)
- Scope note: assemble, index, redact, and quality-check requested evidence for auditor review;
  this package does not test controls or conclude.

## 2. Evidence Request Register (PBC Log)
One row per evidence request (PBC item). `Readiness` is one of `packaged-complete`,
`evidence-gap`, `evidence-stale`, `redaction-required`, `custody-gap`, `needs-data`,
`not-applicable` — never a testing conclusion.

| Request | Title | Control | Readiness | Artifacts |
| ------- | ----- | ------- | --------- | --------- |
| {{request_id}} | {{title}} | {{control_ref}} | {{status}} | {{artifact_refs}} |

## 3. Request-to-Artifact-to-Evidence Mapping
One row per request with the evidence it rests on, its redaction state, and the reason for the
readiness status.

| Request | Evidence refs | Readiness | Redaction | Reason |
| ------- | ------------- | --------- | --------- | ------ |
| {{request_id}} | {{evidence_refs}} | {{status}} | {{redaction_status}} | {{reason}} |

## 4. Packaging Readiness Summary
- Total requests assessed: {{total}}
- packaged-complete / evidence-gap / evidence-stale / redaction-required / custody-gap /
  needs-data / not-applicable: counts
- NOTE: counts describe packaging readiness only and are NOT a control-effectiveness conclusion.

## 5. Open Items and Remediation Register
One row per affected artifact for each `evidence-gap` / `evidence-stale` / `redaction-required` /
`custody-gap` request. Owner/target/severity come from the versioned remediation config, else
`(unassigned)` / `(TBD)` / `medium`.

| Request | Artifact | Issue | Owner | Target date | Severity |
| ------- | -------- | ----- | ----- | ----------- | -------- |
| {{request_id}} | {{artifact_id}} | {{issue}} | {{owner}} | {{target_date}} | {{severity}} |

## 6. Chain of Custody and Redaction Log
Provenance is preserved for every packaged artifact; redaction is logged without altering the
source of record. No raw sensitive values appear here — masked identifiers and pointers only.

| Artifact | Source system | Prepared by | Extracted on | Checksum | Redaction |
| -------- | ------------- | ----------- | ------------ | -------- | --------- |
| {{artifact_id}} | {{source_system}} | {{prepared_by}} | {{extracted_on}} | {{checksum}} | {{redaction}} |

## 7. Source and Citation Index
- Per request: the `{source_system}:{source_ref}@{as_of_date}` citations backing the readiness
  status and the packaged evidence.

## 8. Approvals and Delivery Boundary
- Prepared by: {{prepared_by}}
- Control owner review: {{control_owner_review}} (name or `pending`)
- Audit coordinator sign-off: pending (delivery to the auditor is a separate, human-authorized action)
- Delivered to auditor by this package: NO (`delivered_to_auditor: false`)
- Management assertion made by this package: NO (`management_assertion_made: false`)
- Standing note: draft-only; this package does not conclude on control operating effectiveness.
