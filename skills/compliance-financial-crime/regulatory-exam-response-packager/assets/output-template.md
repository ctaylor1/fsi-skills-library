<!--
Controlled output template for regulatory-exam-response-packager.
Every assembled response package MUST render all ten sections below, in order. The section
headings are a versioned contract: scripts/validate_output.py checks that `template_sections`
in the machine-readable package is a superset of these headings (template fidelity). Do not
rename or drop a section; add jurisdiction-specific detail inside a section instead.
This is a DRAFT for human review and human submission — it is never sent to a regulator by
this skill.
-->

# Regulatory Examination / Inquiry Response Package (DRAFT)

## Examination Identification
- Exam / inquiry ID, regulator/agency, requesting contact, response due date.
- Package version (template + config) and preparation date.

## Scope and Period
- Examination scope statement and the review period (`from`–`to`).
- Any scope caveats or agreed limitations.

## Request-Response Index
Mapping table, one row per regulator request:

| Request ID | Prompt (short) | Category | Coverage | Response status |
| ---------- | -------------- | -------- | -------- | --------------- |
| REQ-nn | … | document / information / question / finding-response | complete / partial / needs-evidence / gap | draft-ready-for-review / needs-approval / unsupported-assertion / needs-evidence / incomplete |

## Response Narratives
Per request: the drafted narrative. **Every factual assertion carries an inline source
citation.** Any assertion without provenance is listed under Outstanding Items, and its request
is marked `unsupported-assertion` — it is never presented as ready.

## Evidence Register
Per request: each evidence item with `evidence_id`, description, source/provenance reference,
and data classification. Restricted material (e.g., SAR-related) is handled per the
confidentiality rules in `references/controls.md`.

## Issue and Remediation Status
For findings / MRAs / self-identified issues: current status, owner, target date, and the
source of that status. Status is reported, never adjudicated or closed here.

## Approvals and Sign-offs
Per request and for the package: required approver roles, who approved, status, and date.
An item is only `draft-ready-for-review` when **all** required roles are recorded as approved.

## Source Map and Provenance
The authoritative source for each cited item (system, reference, date/version). See
`references/source-map.md` for the source hierarchy and citation format.

## Outstanding Items and Gaps
Everything not yet ready: gaps (no response), missing evidence, unsupported assertions, and
items awaiting approval — with exactly what is needed to close each. Nothing is hidden.

## Draft Status and Limitations
Standing note (verbatim): *"Draft response package only; not submitted to any regulator, no
exam item closed, and no system of record updated."* Names the human owner responsible for
review and for any submission to the regulator.
