---
name: credit-application-packager
description: >-
  Assemble borrower financials, collateral, application data, recorded approvals, and
  underwriting open items into a single source-linked credit application package (a draft
  deliverable) for credit-analyst and underwriter review. Use when a commercial or consumer
  credit/lending analyst asks to build, organize, compile, or package a loan or credit
  application file, map documents to required package components, capture recorded approvals
  and outstanding conditions, flag borrower/entity inconsistencies, or produce an
  underwriting-ready package index with citations. HARD BOUNDARY: draft-only — this skill
  never makes or communicates a credit decision, approval, denial, or adverse-action notice;
  never certifies package completeness (formal pre-underwriting or closing completeness
  certification is a separate control); never fabricates or infers missing borrower data;
  and never submits, sends, files, or delivers the package. It assembles and flags open
  items; humans review, certify, and decide.
license: MIT
compatibility: Amazon Quick Desktop; requires core-banking, CRM, document-intelligence, loan-origination/servicing, product-terms, and approved-calculation MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Banking"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Draft & package"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 2 - analytical production"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Banking product & credit operations"
  aws-fsi-primary-user: "Commercial or consumer credit analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Credit Application Packager

## Purpose and outcome
Turn a pile of borrower documents, spreads, collateral records, application data, recorded
approvals, and open conditions into ONE **source-linked, underwriting-ready credit package
draft**. For each required package component the skill maps the supporting document, records
its assembly status (`included`, `stale`, `unresolved`, or `open-item`), checks that the
borrower/entity is consistent across documents, captures recorded approvals and outstanding
conditions, and compiles an explicit open-items list — every asserted item carries a
citation. The outcome is a package a human can review and route: a rendered package from
[assets/output-template.md](assets/output-template.md) plus a machine-readable manifest.
The skill **assembles**; it does not certify completeness and does not decide credit.

## Use when
- "Build / compile / package the credit application file for this borrower."
- "Organize these financials, tax returns, collateral, and approvals into an underwriting package."
- "Map the documents we have to the required package components and list what's missing."
- "Capture the recorded approvals and outstanding conditions on this deal."
- "Produce a source-linked package index with citations for the underwriter."

## Do not use
- **Formal completeness certification** (product/policy/legal/signature/expiration checklist
  sign-off before underwriting or closing) → `loan-package-completeness-checker`.
- **Credit memorandum drafting** (repayment analysis, risk narrative, recommendation) →
  `credit-memo-drafter`.
- **Spreading financial statements / tax returns** into templates → `financial-spreading-assistant`.
- **Statement extraction** (income, obligations, cash-flow trends) → `bank-statement-analyzer`.
- **KYC / onboarding document checking** → `customer-onboarding-document-checker`.
- Any **credit decision, approval, denial, adverse-action, or affordability determination**
  → refuse; route to the underwriter / licensed decisioner (see `loan-affordability-precheck`
  for indicative-only affordability).

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Packaging is deliberately separated
from completeness certification and from credit decisioning (distinct controls, entitlements,
and accountability). This skill emits a durable `package_id` + assembled manifest and hands
off to `loan-package-completeness-checker` for formal certification; it must not perform the
checker's or the underwriter's work.

## Inputs and prerequisites
- The intake bundle: `package_id`, product, jurisdiction, `required_components`, the borrower
  profile, the available `documents` (each with component, doc_id, effective/expiration
  dates, borrower identity, and a `source_ref`), recorded `approvals`, `required_approvals`,
  outstanding `conditions`, and an `as_of_date`. Schema and required fields:
  [scripts/validate_input.py](scripts/validate_input.py).
- Read access to core banking, CRM, document intelligence, loan origination/servicing, and
  product-terms sources (all read-only). No document is fabricated: what is not supplied
  becomes an open item.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The loan origination system is the
system of record for the application, approvals, and conditions; document intelligence
provides the underlying documents and citations; product terms define which components are
required. Cite every included item as `{system}:{ref}@{date/version}`. `required_components`,
`required_approvals`, and the package template are **versioned contracts**.

## Workflow
1. **Validate & normalize** — run `validate_input`; confirm the intake structure and surface
   data gaps (missing effective dates, missing borrower identity on a document) as warnings.
2. **Assemble the package (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): map each required
   component to its supporting document, set the assembly status, run the borrower/entity
   consistency check, capture recorded approvals + outstanding required approvals, list
   outstanding conditions, and build the citation source index. Rules:
   [references/domain-rules.md](references/domain-rules.md).
3. **Render the package** — populate [assets/output-template.md](assets/output-template.md)
   from the manifest; every included figure/document carries its citation.
4. **Compile open items** — everything not `included` (missing components, stale documents,
   unresolved identities, outstanding approvals/conditions) becomes an explicit open item for
   the analyst and underwriter. Do not silently drop or infer.
5. **Mark draft & hand off** — set `assembly_status: draft-assembled`, record that human
   approval is required before delivery, and route to `loan-package-completeness-checker` for
   formal certification. Never certify, decide, or send.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check enforces: all required template sections present; every asserted
(included/stale/unresolved) item carries a citation (no unsupported/unapproved claims);
approvals are recorded with role, date, and citation; no credit-decision, completeness-
certification, or send/submit language; `assembly_status` is `draft-assembled` and delivery
approval is flagged as required; standing note present. Fail closed on any miss.

## Human approval
`external-delivery`. This skill produces a **draft** package for internal review. A human must
review and approve before the package is delivered, relied on for underwriting, or treated as
a system-of-record change. Formal completeness certification and the credit decision are
separate, human-owned control steps — this skill neither performs nor pre-empts them.

## Failure handling
- **Missing required component** → status `open-item` (missing); listed, never fabricated.
- **Stale document** (past its expiration/effective window vs `as_of_date`) → status `stale`;
  flagged for refresh, still cited.
- **Borrower/entity mismatch across documents** → status `unresolved`; flagged for human
  reconciliation; never auto-merged.
- **Missing recorded approval** → captured as an outstanding required approval + open item;
  never assumed granted.
- **Unresolvable data / tool timeout** → return the partial package with an explicit
  incomplete flag and the open-items list; no retry assumption, no guessing.

## Output contract
See [references/controls.md](references/controls.md) and
[assets/output-template.md](assets/output-template.md).
1. **Rendered package** — the template sections (summary, borrower profile, application,
   financial information, collateral, KYC/onboarding, approvals, open items, source index)
   populated with cited content.
2. **Machine-readable manifest** — `package_id`, per-component assembly status + citation,
   approvals (recorded/outstanding), open items, source index, `assembly_status`
   (`draft-assembled`), and `human_approval_required_before_delivery: true`.
3. **Open-items list** — every missing/stale/unresolved/outstanding item with a required
   human action.
4. **Standing note** — "Draft credit package for human review only. This package is not a
   completeness certification, not a credit decision or adverse-action notice, and has not
   been submitted or delivered."

## Privacy and records
**Highly Confidential — customer NPI/PII.** Mask borrower and account identifiers in output
to what the package requires; do not expose full account numbers or government IDs. Retain the
package manifest, citations, and config versions per the bank's credit-file recordkeeping
policy. Log every read and every package assembly with the analyst identity. Data stays within
the deployment's residency boundary.

## Gotchas
- **Packaging ≠ certification.** Assembling and indexing documents is not a statement that the
  package is complete or compliant. Formal completeness certification is
  `loan-package-completeness-checker`; this skill only reports assembly status and open items.
- **Packaging ≠ decision.** Never state or imply an approval, denial, adverse action, or that
  the borrower qualifies. Those are the underwriter's, recorded via the approval broker.
- **No document is invented.** A component with no supporting source is an open item, not an
  assumed inclusion. Every included item must be citable.
- **Identity mismatches are unresolved, not merged.** Conflicting borrower name/ID across
  documents is surfaced for a human, never silently reconciled.
- **Approvals are recorded, never assumed.** A required approval with no record is outstanding
  and appears as an open item.
- **Versioned contracts.** Record `required_components`, `required_approvals`, and template
  versions on the manifest so the assembly is reproducible and reviewable.
