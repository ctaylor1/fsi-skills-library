---
name: pci-dss-evidence-assistant
description: >-
  Map PCI DSS v4.0.1 requirements to your controls and evidence, flag coverage gaps and
  stale evidence, and assemble an assessor-ready DRAFT evidence package (requirement-to-
  control-to-evidence mapping, gap/remediation register, source index) for a QSA/ISA-led
  assessment. Use when a PCI program manager or security/compliance analyst needs to prepare
  for a PCI DSS assessment or SAQ, inventory which requirements have current evidence, build
  a gap and remediation register, or organize evidence for an assessor or internal audit.
  HARD BOUNDARY: draft support only — this skill NEVER attests or determines PCI DSS
  compliance, never marks a requirement "In Place", never signs or submits an AOC, ROC, or
  SAQ, and never sends the package externally. Every compliance determination and
  attestation stays with a Qualified Security Assessor (QSA), authorized ISA, or the
  organization's authorized signer.
license: MIT
compatibility: Amazon Quick Desktop; requires PCI-standard/SAQ-template retrieval, GRC/evidence-repository, vulnerability-scanner (ASV/internal), configuration/CMDB, IAM, and ticketing/case-management MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Payments"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Draft & package"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 2 - analytical production"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII; cardholder data)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Payments operations & risk"
  aws-fsi-primary-user: "PCI program manager / security or compliance analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# PCI DSS Evidence Assistant

## Purpose and outcome
Turn a scattered set of PCI DSS controls and evidence artifacts into a single, assessor-ready
**draft evidence package**: each in-scope requirement mapped to its controls and cited
evidence, coverage gaps and stale evidence flagged, and a gap/remediation register assembled.
The outcome is a package a PCI program manager can review and hand to a **QSA or authorized
ISA** for assessment — the skill never attests, never determines a requirement *In Place*,
and never signs or submits an AOC/ROC/SAQ.

## Use when
- "Assemble the PCI DSS evidence package for our upcoming assessment / SAQ."
- "Map requirements to controls and evidence and show me what's missing."
- "Which requirements have stale or missing evidence? Build a gap and remediation register."
- "Organize our PCI evidence for the QSA / for internal audit."

## Do not use
- **Formal assessment / determination** (marking requirements *In Place* / *Not In Place*) →
  a QSA or authorized ISA, not a skill.
- **Signing or submitting** an AOC, ROC, or SAQ, or emailing the package to an acquirer/brand
  → the organization's authorized signer, with human approval (never this skill).
- **Producing the underlying evidence** — vulnerability triage → `vulnerability-prioritization-assistant`;
  cloud config → `cloud-security-posture-reviewer`; access reviews → `identity-access-reviewer`;
  TPSP assurance → `third-party-cyber-risk-reviewer`.
- **Scope validation** of the CDE → QSA/ISA activity.
- Any request to **attest compliance** or fabricate/assume evidence → refuse; fail closed.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Evidence assembly is separated from the
specialist reviews that *produce* evidence and from the *assessment/attestation* that consumes
the package. Downstream consumers include `regulatory-exam-response-packager` (QSA RFI/exam),
`audit-evidence-packager` (internal audit), `policy-procedure-gap-analyzer`, and
`risk-control-self-assessment-assistant`. Attestation is a human QSA/authorized-signer step,
never a skill.

## Inputs and prerequisites
- A requirements/controls/evidence file: assessment metadata (DSS version, SAQ/ROC type,
  period, `as_of_date`, preparer), controls with evidence items (id, type, `effective_date`,
  `source_ref`), requirement-to-control mapping, optional N/A justifications, and optional
  versioned freshness-window + remediation config. Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Read access to the GRC/evidence repository, scanners, CMDB, IAM, and ticketing.
- **No cardholder data (PAN/SAD)** — supply evidence pointers and masked identifiers only.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The GRC/evidence repository is the
system of record for control-to-evidence mapping; the PCI DSS standard + SAQ/ROC templates are
versioned contracts (pin the DSS version). Cite every evidence item as
`{source_system}:{source_ref}@{effective_date}`. Freshness-window config is versioned and
recorded on every package.

## Workflow
1. **Validate input** — run [scripts/validate_input.py](scripts/validate_input.py); fail
   closed on structural problems; note data gaps that will force `needs-data` / `evidence-gap`
   / `evidence-stale`.
2. **Map & assess (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): for each
   requirement, gather mapped-control evidence, compute freshness vs. the per-type window, and
   assign an **evidence-readiness** status (`evidence-complete` | `evidence-gap` |
   `evidence-stale` | `needs-data` | `not-applicable`). Precedence and windows:
   [references/domain-rules.md](references/domain-rules.md).
3. **Build the register** — one gap/remediation row per affected control, with owner/target/
   severity from config (or `(unassigned)`/`(TBD)`/`medium`).
4. **Render the package** — populate every section of
   [assets/output-template.md](assets/output-template.md): scope, CDE summary, mapping,
   readiness summary, gap register, assumptions, citation index, approvals + attestation
   boundary, standing note.
5. **Validate output** — run [scripts/validate_output.py](scripts/validate_output.py); correct
   and repeat until it passes or fail closed.
6. **Hand off** — return the draft to the program manager for review; never send or submit.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py) after.
The output check enforces: template fidelity (all eight sections present); no unsupported
claims (every `evidence_ref` exists in the evidence index; complete/stale requirements cite
evidence; gaps recorded in the register); no attestation/determination language; required
approvals recorded with `attestation_made: false`; standing non-attestation note present. Fail
closed on any miss.

## Human approval
`external-delivery`. Internal assembly and review of the draft is reviewer-sampled. **Human
approval is required before any external delivery** (to a QSA, acquirer, or card brand) or any
system-of-record change. The formal assessment (*In Place* determinations) and the AOC/ROC/SAQ
attestation are separate, human-only actions performed by a QSA/authorized ISA and the
authorized signer — this skill proposes and packages; humans assess and attest.

## Failure handling
- **Unmapped requirement** → `needs-data`; list the requirement. Never assume coverage.
- **No evidence for a mapped control** → `evidence-gap`; record in the register.
- **Undatable / expired evidence** → treated as **stale** (`evidence-stale`); cite it for
  refresh. Never counted as fresh.
- **N/A without documented justification** → `needs-data` (PCI requires justification).
- **Conflicting evidence versions** → cite both; surface for the reviewer; do not pick a
  winner.
- **Tool timeout / partial pull** → return the partial package with an explicit incomplete
  flag; no retry assumption.

## Output contract
1. **Evidence package (draft document)** — the eight required sections from
   [assets/output-template.md](assets/output-template.md), headers verbatim.
2. **Requirement records** — per requirement: `req_id`, mapped `control_ids`,
   `evidence_status`, `readiness_reason`, `evidence_refs`, and citations.
3. **Gap/remediation register** — per affected control: issue, owner, target date, severity.
4. **Evidence-readiness summary** — counts by status (explicitly *not* a determination).
5. **Approvals block** — `prepared_by`, `compliance_reviewer` (name or `pending`),
   `qsa_or_isa_signoff` slot, `attestation_made: false`.
6. **Machine-readable** — the full package JSON keyed by requirement, with the
   `config_version` and freshness-window version.
7. **Standing note** — "Draft evidence support only; this package does not attest PCI DSS
   compliance ...". See [references/controls.md](references/controls.md).

## Privacy and records
**Highly Confidential (customer NPI/PII; cardholder data).** Never place PAN or SAD in the
package — use tokenized/masked identifiers and evidence *pointers* only. Store control metadata
and citations, not cardholder data. Retain the package, its `config_version`, freshness-window
version, and citations per the organization's PCI evidence-retention policy; log the preparer
identity on every build. See [references/controls.md](references/controls.md).

## Gotchas
- **Readiness ≠ compliance.** `evidence-complete` means the evidence is assembled and current,
  ready for a QSA to assess — it is **not** "In Place" and not an attestation.
- **Stale beats optimism.** Undatable or expired evidence is stale, not fresh; a quarterly ASV
  scan or a 6-monthly review silently ages out — the freshness window catches it.
- **Gap outranks staleness.** A missing control is `evidence-gap` even if other controls are
  current; do not let one good control mask a missing one.
- **N/A needs a reason.** An unjustified N/A is `needs-data`, never a free pass.
- **No cardholder data in evidence.** Reference tokens/masked PANs and artifact pointers; the
  package must never carry PAN/SAD.
- **Draft-only, never send.** The skill hands the package to a human; it never emails, submits,
  or signs.
