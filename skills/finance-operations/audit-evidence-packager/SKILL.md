---
name: audit-evidence-packager
description: >-
  Collect, index, redact, cross-reference, and quality-check requested audit evidence and
  assemble a reviewer-ready DRAFT evidence package (PBC request-to-artifact-to-evidence
  mapping, chain-of-custody and approval history, redaction log, open-items register, source
  index) for an internal audit, SOX walkthrough, financial-statement audit, or regulatory
  exam. Use when an audit coordinator or control owner needs to respond to a PBC / evidence-
  request list, organize workpaper evidence, confirm each request is supported by in-period
  artifacts with preserved provenance, or flag gaps / stale / unredacted / broken-custody
  items for auditor review. HARD BOUNDARY: draft support only — NEVER concludes on control
  operating effectiveness, issues an audit opinion, signs a management representation or
  attestation, delivers or submits the package, or fabricates, infers, or over-redacts
  evidence. Testing, opinions, and attestation stay with the auditor, control owner, or
  authorized signer.
license: MIT
compatibility: Amazon Quick Desktop; requires GRC/audit-workpaper and evidence-repository, ERP/GL, subledger, consolidation, FP&A, and regulatory-reporting systems, document-intelligence (redaction), and case-management (chain of custody) MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Finance & Operations"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Draft & package"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 2 - analytical production"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Confidential (financial records)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Finance & Controllership"
  aws-fsi-primary-user: "Audit coordinator / control owner"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Audit Evidence Packager

## Purpose and outcome
Turn a scattered PBC ("prepared by client") / evidence-request list and a pile of workpaper
artifacts into a single, reviewer-ready **draft evidence package**: each request mapped to its
supporting artifacts and cited evidence, chain of custody and approval history preserved,
sensitive fields redacted, and every gap, stale, unredacted, or broken-custody item flagged in
an open-items register. The outcome is a package an **audit coordinator or control owner** can
review and hand to the auditor — the skill never tests a control, concludes on operating
effectiveness, issues an opinion, signs a representation, or delivers the package.

## Use when
- "Assemble the evidence package for the FY26 SOX walkthrough / internal audit / regulatory exam."
- "Map each PBC request to its supporting artifacts and show me what's missing."
- "Which requests have stale, unredacted, or missing evidence? Build the open-items register."
- "Organize the workpaper evidence with chain of custody for the auditor."
- "Redact the PII in this sample and index it against the request list."

## Do not use
- **Testing or concluding** on a control (operating-effectiveness determination, exception
  disposition, audit opinion) → the auditor / engagement team, not a skill.
- **Signing or submitting** a management representation, or **delivering** the package to the
  auditor / regulator → the control owner or authorized signer, with human approval (never this
  skill).
- **Producing the underlying evidence** — a reconciliation break/tie-out → `gl-reconciler`;
  normalized financials → `financials-normalizer`; close artifacts → `month-end-close-orchestrator`;
  regulatory-report data checks → `regulatory-reporting-data-validator`.
- **The financial-statement audit workpaper itself** → `financial-statement-audit-assistant`
  consumes this package.
- Any request to **fabricate/assume evidence** or **over-redact to hide** an artifact → refuse;
  fail closed.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Evidence assembly is separated from the
skills that *produce* the underlying evidence and from the *testing/attestation* that consumes
the package. This skill emits a draft package keyed by `config_version` with a durable
per-request `request_id`; downstream consumers work the same package rather than rebuilding it.
Testing, the audit opinion, and the management representation are human/auditor actions, never a
skill.

## Inputs and prerequisites
- An evidence-request / artifact-catalog file: engagement metadata (framework, `audit_period`,
  `as_of_date`, preparer), an artifact catalog (each with `type`, dates, `source_ref`, a
  `chain_of_custody` block, optional `sensitive_fields` + `redaction`, `superseded_by`), the PBC
  request list with `artifact_refs` and per-request `period`, optional N/A justifications, and an
  optional versioned remediation config. Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Read access to the GRC/audit-workpaper and evidence repository, ERP/GL and subledgers, FP&A,
  regulatory-reporting systems, document intelligence (redaction), and case management (custody).
- **No raw sensitive values in the package** — supply evidence *pointers* and masked identifiers;
  flag any PII/NPI columns in `sensitive_fields` so redaction is enforced.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The GRC/audit-workpaper repository is
the system of record for request-to-artifact mapping and custody; the ERP/GL and subledgers are
authoritative for the underlying financial artifacts. Cite every artifact as
`{source_system}:{source_ref}@{as_of_date}`. The remediation config is versioned and recorded on
every package. Never substitute an unsourced assertion for a cited artifact.

## Workflow
1. **Validate input** — run [scripts/validate_input.py](scripts/validate_input.py); fail closed
   on structural problems; note gaps that will force `needs-data` / `evidence-gap` /
   `evidence-stale` / `redaction-required` / `custody-gap`.
2. **Map, redact & quality-check (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): for each request,
   resolve the mapped artifacts, confirm chain of custody, enforce redaction of flagged sensitive
   fields, check period coverage, and assign a **packaging readiness** status
   (`packaged-complete` | `evidence-gap` | `evidence-stale` | `redaction-required` |
   `custody-gap` | `needs-data` | `not-applicable`). Precedence:
   [references/domain-rules.md](references/domain-rules.md).
3. **Build the registers** — an open-items / remediation register (one row per affected artifact)
   and a chain-of-custody + redaction log (provenance preserved without altering the source).
4. **Render the package** — populate every section of
   [assets/output-template.md](assets/output-template.md): scope, PBC register, mapping, readiness
   summary, open items, custody/redaction log, citation index, approvals + delivery boundary,
   standing note.
5. **Validate output** — run [scripts/validate_output.py](scripts/validate_output.py); correct and
   repeat until it passes or fail closed.
6. **Hand off** — return the draft to the audit coordinator / control owner for review; never send,
   submit, or sign.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py) after.
The output check enforces: template fidelity (all eight sections present); completeness and no
unsupported claims (every `evidence_ref` exists in the evidence index; `packaged-complete`
requests cite evidence *and* every cited artifact carries a complete chain of custody; open items
appear in the register); redaction integrity (no `packaged-complete` request has unresolved
redaction); no audit-conclusion / opinion / management-representation / delivery language; required
approvals recorded with `delivered_to_auditor: false` and `management_assertion_made: false`; and
the standing non-conclusion note. Fail closed on any miss.

## Human approval
`external-delivery`. Internal assembly and review of the draft is reviewer-sampled. **Human
approval is required before any external delivery** (to the auditor, regulator, or committee) or
any system-of-record change. Testing and the operating-effectiveness conclusion, the audit
opinion, and the AOC/management representation are separate, human-only actions performed by the
auditor, control owner, or authorized signer — this skill proposes and packages; humans test,
conclude, and attest.

## Failure handling
- **Unmapped request** → `needs-data`; list the request. Never assume coverage.
- **Referenced artifact absent from the repository** → `evidence-gap`; record in the register.
- **Sensitive fields flagged but not redacted** → `redaction-required`; the item is not packaged
  until redaction is applied and logged. Never leak raw PII/NPI.
- **Incomplete chain of custody** (missing source/preparer/extraction/checksum) → `custody-gap`;
  provenance cannot be certified.
- **Artifact out-of-period or superseded** → `evidence-stale`; cite it so the reviewer can refresh.
- **Conflicting artifact versions** → cite both; surface for the reviewer; do not pick a winner.
- **Tool timeout / partial pull** → return the partial package with an explicit incomplete flag;
  no retry assumption.

## Output contract
1. **Evidence package (draft document)** — the eight required sections from
   [assets/output-template.md](assets/output-template.md), headers verbatim.
2. **Request records** — per request: `request_id`, mapped `artifact_refs`, `evidence_status`,
   `readiness_reason`, `redaction_status`, `evidence_refs`, and citations.
3. **Open-items / remediation register** — per affected artifact: issue, owner, target date,
   severity.
4. **Chain-of-custody + redaction log** — per artifact: source system, preparer, extraction date,
   checksum, redaction status.
5. **Packaging-readiness summary** — counts by status (explicitly *not* a control conclusion).
6. **Approvals block** — `prepared_by`, `control_owner_review` (name or `pending`),
   `audit_coordinator_signoff` slot, `delivered_to_auditor: false`, `management_assertion_made: false`.
7. **Machine-readable** — the full package JSON keyed by request, with the `config_version`.
8. **Standing note** — "Draft evidence support only; this package does not conclude on control
   operating effectiveness ...". See [references/controls.md](references/controls.md).

## Privacy and records
**Confidential (financial records); may include employee/customer PII/NPI in sampled artifacts.**
Never place raw sensitive values in the package — flag them in `sensitive_fields`, enforce
redaction, and reference masked identifiers and evidence *pointers* only. Preserve chain of custody
(source, preparer, extraction timestamp, checksum) so provenance is auditable; redaction is logged
and never alters the source of record. Retain the package, its `config_version`, custody log, and
citations per the organization's audit-evidence retention policy; log the preparer identity and any
external-delivery approval. See [references/controls.md](references/controls.md).

## Gotchas
- **Readiness ≠ effectiveness.** `packaged-complete` means the evidence is assembled, in-period,
  custody-preserved, and redacted — ready for the auditor to test. It is **not** a conclusion that
  the control operates effectively, and not an opinion.
- **Redaction is a gate, not a courtesy.** A flagged-but-unredacted artifact is `redaction-required`
  and is never packaged; the package must never carry raw PII/NPI. Over-redacting to obscure an
  artifact is equally prohibited.
- **Custody outranks convenience.** An artifact with a missing source, preparer, extraction date, or
  checksum is `custody-gap`; you cannot certify what you cannot trace.
- **Gap and staleness are ordered.** A missing artifact is `evidence-gap` even if others are current;
  an out-of-period or superseded artifact is `evidence-stale`, never quietly counted as current.
- **N/A needs a reason.** An unjustified N/A is `needs-data`, never a free pass.
- **Draft-only, never deliver.** The skill hands the package to the coordinator/owner; it never
  emails, submits, signs, or concludes.
