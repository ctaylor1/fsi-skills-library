# Domain Rules — model-risk-documenter

Orientation references: SR 11-7 (Supervisory Guidance on Model Risk Management), OCC 2011-12,
NIST AI RMF, and ISO/IEC 42001. The firm's **model-risk framework and documentation template**
take precedence and are a versioned contract (`template_version` / `framework_version`). All of
the logic below is configuration, not judgment — a reviewer may override during adjudication,
but the draft states the computed value. This skill **documents and traces evidence**; it does
not test, validate, approve, or attest.

## Required documentation sections (all ten, always assembled)

`purpose`, `methodology`, `data`, `performance`, `limitations`, `controls`, `monitoring`,
`changes`, `approvals`, `traceability`. A pack missing any section entirely is `needs-data`,
not a completed pack.

## Section status (deterministic)

For each section, from its `content_ref`, `source_artifacts`, and `coverage`:

| Condition | Section status |
| --------- | -------------- |
| No `content_ref` | **needs-data** (missing documentation) |
| Content present, but no **versioned** source artifact | **gap** (untraceable) |
| Content present, cited, but a required coverage element is missing | **gap** (coverage gap) |
| Content present, cited, and all required coverage present | **documented** |

A source artifact earns a citation **only if it has both an `artifact_id` and a `version`**; an
unversioned artifact is untraceable and gives no credit. Citations use the
`{artifact_type}:{artifact_id}@{version}` format.

### Required coverage (methodology & limitations)

To count as `documented`, these two sections must carry all listed coverage elements (this is
the "methodology and limitation coverage" control):

| Section | Required coverage elements |
| ------- | -------------------------- |
| `methodology` | `conceptual_soundness`, `assumptions` |
| `limitations` | `known_limitations`, `use_constraints` |

## Findings (open items requiring adjudication)

Two finding sources, all emitted with `status: open` and `adjudication_required: true`:

- **Carried validation findings** — any open finding supplied in the intake is carried through
  **unchanged and open**; it is never closed, resolved, or waived here.
- **Documentation-gap findings** — one open finding per `gap`/`needs-data` section:
  `needs-data` → **High** severity, `gap` → **Medium**. Each carries a `recommended_remediation`
  (a section default), an `owner`, and `source_refs` that include the template requirement
  (`template:model-doc@{template_version}#{section}`) plus any partial section citations, so
  every finding is itself sourced.

## Approvals — no false attestation

The pack **records only approvals that carry a citation** (`reference`). An approval without a
cited memo is **not** transcribed as evidence; it is surfaced in `unsupported_approvals` and
flagged. The pack's own attestation block is always emitted `pending` — the skill records what
approvals *exist*, it does not itself approve or attest that the model is validated or fit for
use. A recorded **unconditional `approved`** decision may not coexist with an open High-severity
finding (finding/approval inconsistency).

## Readiness roll-up and approver routing

`readiness` is the deterministic roll-up:

| Condition (in order) | readiness |
| -------------------- | --------- |
| Any section is `gap` or `needs-data` | **documentation-gaps** |
| Else any open finding is High severity | **outstanding-findings** |
| Else | **draft-complete-pending-review** |

`pack_status` is `needs-data` if any section is `needs-data` (or a required section is absent),
else `draft-pack`. Attestation `status` is always `pending`; approver routing is by model tier:

| Model tier (materiality) | Required approvers |
| ------------------------ | ------------------ |
| **Tier 1** | Model Risk Management (independent validation); Model Risk Committee |
| **Tier 2** | Model Risk Management (independent validation); Model Owner |
| **Tier 3** | Model Owner |

## Hard boundaries (fail closed)

- No **validation, approval, attestation, certification, or fitness-for-use / deployment
  clearance** of the model.
- No **final / binding determination** that the model is validated or its documentation
  complete; the section statuses and readiness are computed recommendations.
- No **closing / resolving / waiving** a finding.
- No **false attestation**: never record an approval without a cited reference; never mark a
  section `documented` without a versioned source artifact.
- No **guessing / fabrication**: a missing section, missing content, or unversioned artifact is
  a `gap`/`needs-data`, never silently filled.
