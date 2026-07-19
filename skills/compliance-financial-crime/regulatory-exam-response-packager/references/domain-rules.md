# Domain Rules — regulatory-exam-response-packager

Orientation references: BSA/FinCEN recordkeeping and SAR-confidentiality; prudential
examination practice (e.g., request-list / MRA response workflows). The firm's exam-management
standard, its response **template + required-approver config**, and legal guidance take
precedence and are versioned contracts.

## Coverage classification (deterministic, documented)

Coverage describes how complete a request's response is; it is configuration, not judgment.

| Condition (evaluated in order) | Coverage | Response status |
| ------------------------------ | -------- | --------------- |
| No response mapped to the request | `gap` | `incomplete` |
| `evidence_required` and no evidence provided | `needs-evidence` | `needs-evidence` |
| Narrative missing (evidence present) | `partial` | `incomplete` |
| Any assertion lacks a `source_ref` | `partial` | `unsupported-assertion` |
| Complete + sourced, but a required approver role not `approved` | `complete` | `needs-approval` |
| Complete, sourced, and fully approved | `complete` | `draft-ready-for-review` |

`evidence_required` defaults to true for `document` and `finding-response` categories and is
explicit per request. A `question` may be answered by a sourced narrative alone.

## Provenance and assertion rules

- **Every factual assertion carries a `source_ref`.** An assertion without one is `unsupported`
  and its request cannot be `draft-ready-for-review` — it is surfaced under Outstanding Items.
- **Every evidence item carries a `source_ref`** (provenance is mandatory; enforced in
  `validate_input.py`).
- Citations on an item are the de-duplicated union of its assertion and evidence source
  references.

## Approval rules

- `required_approver_roles` (e.g., `compliance-owner`, `legal`) come from config.
- An item is ready only when **all** required roles are recorded as `approved`; a missing role
  makes it `needs-approval`. The skill records approvals — it never supplies them.

## Hard boundaries (fail closed)

- No **submission / sending / transmission** of the response to the regulator.
- No **closure or resolution** of the exam, an inquiry, an item, a finding, or an MRA.
- No **regulated attestation/certification** on the institution's behalf.
- No **unsupported assertion** presented as ready; no **unapproved** item presented as ready.
- No **tipping-off**: never reveal SAR existence/subject detail or draft customer-facing
  monitoring/SAR disclosures.
- No **system-of-record write**.

## Package contents — required sections

The assembled package renders all ten sections of `assets/output-template.md`: Examination
Identification; Scope and Period; Request-Response Index; Response Narratives; Evidence
Register; Issue and Remediation Status; Approvals and Sign-offs; Source Map and Provenance;
Outstanding Items and Gaps; Draft Status and Limitations.
