---
name: loan-package-completeness-checker
description: >-
  Verify a loan underwriting or closing package against product, policy, approval,
  collateral, legal, signature, expiration, and jurisdiction checklists; surface missing
  documents, uncleared conditions, cross-document inconsistencies, expired items, and
  exceptions with cited evidence and a severity-ranked readiness view for a human certifier.
  Use when a loan operations analyst, underwriter, or closer asks "is this loan package
  complete", "what conditions are still outstanding", "check this closing package before
  certification", or needs a pre-certification completeness review. This skill produces
  completeness findings and cited evidence ONLY; it NEVER approves or denies a loan, issues
  a clear-to-close or adverse action, waives a condition, certifies/closes/funds/books the
  loan, or writes a system of record — a qualified human must adjudicate and certify.
license: MIT
compatibility: Amazon Quick Desktop; requires loan-origination/closing-system, document-intelligence, entity-resolution, controlled-checklist/register, and approved-calculation MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Banking"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Banking product & credit operations"
  aws-fsi-primary-user: "Loan operations / underwriter / closer"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Loan Package Completeness Checker

## Purpose and outcome
Given an underwriting or closing package for a loan, evaluate it against the applicable
**product and jurisdiction checklist** and produce a **completeness assessment**: a list of
findings — missing documents, missing signatures, expired items, cross-document
inconsistencies, approval-envelope breaches, and outstanding conditions — each carrying a
**severity** (Blocker / Exception / Advisory) and **cited evidence**, plus a deterministic
**readiness disposition** for a human certifier. A successful output lets a loan operations
analyst, underwriter, or closer see exactly what is missing or inconsistent before they
certify the package. The certification decision, and any system-of-record write, remains
human.

## Use when
- "Is this loan package complete / ready for certification?"
- "What conditions are still outstanding on this file?"
- "Check this closing package for missing signatures or expired documents."
- "Do the note, closing disclosure, and approval agree on amount, rate, and borrower?"
- A closer or QC reviewer needs a consistent, cited pre-certification checklist result.

## Do not use
- The user wants a **credit decision** ("approve/deny this loan"), a **clear-to-close**, an
  **adverse-action** determination, a **condition waiver**, or to **certify/close/fund/book**
  the loan → out of scope; produce findings and route to the authorized human. Affordability
  screening belongs to `loan-affordability-precheck`; the credit narrative belongs to
  `credit-memo-drafter`.
- Assembling the application package from raw inputs (not checking a finished one) →
  `credit-application-packager`.
- **Fee / APR / TRID tolerance** math on the closing disclosure → `fee-and-charge-reviewer`.
- **KYC/CDD identity** verification or **beneficial-ownership** confirmation →
  `kyc-customer-due-diligence-screener` / `beneficial-ownership-verifier`.
- Post-closing **covenant** tracking → `covenant-compliance-monitor`; post-booking
  **servicing exceptions** → `loan-servicing-exception-resolver`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a completeness
assessment with a durable `assessment_id`; upstream packagers feed it and downstream
skills consume its findings. It must not duplicate their decisions, calculations, or actions.

## Inputs and prerequisites
- A **loan package** for one loan: `loan_id`, `package_type` (underwriting|closing), the
  certification `as_of` date, `jurisdiction`, `product`, `expected_terms`, `approval`, the
  applicable `checklist`, the `documents` on file, and `conditions`. Schema and field
  detail: [scripts/validate_input.py](scripts/validate_input.py) and
  [references/source-map.md](references/source-map.md).
- The **checklist is a versioned contract** for the product + jurisdiction; record its
  version. Validity windows, required signers, and severity mapping are configuration, not
  ad-hoc judgment (see [references/domain-rules.md](references/domain-rules.md)).
- Read access to the loan-origination/closing system, document intelligence, and entity
  resolution.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The executed/received documents in
the origination/closing system are the position of record; the approval terms and the
versioned checklist define what is required; entity resolution normalizes names and
addresses for the consistency check. Cite every finding to a document, checklist item, or
condition id.

## Workflow
1. **Scope & validate** — confirm the loan, package type, jurisdiction, and `as_of`; load
   the package and run [scripts/validate_input.py](scripts/validate_input.py). Fail closed
   on structural errors; note data-quality warnings that limit evaluability.
2. **Run the engine (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to evaluate
   checklist coverage, signatures, expiration, cross-document consistency, the approval
   envelope, and conditions. Each finding returns its severity and the evidence behind it.
3. **Assemble evidence** — for each finding, attach the specific document / checklist item /
   condition and its citation. Findings are **explainable**, not a black-box score.
4. **Derive readiness (deterministic)** — map the finding severities to a readiness band
   (Not-ready / Conditional / Complete) per the documented mapping. This is a **completeness
   recommendation for a human**, explicitly not a lending decision or a certification.
5. **Write the assessment** — plain-language finding list ordered by severity + the evidence
   + the certifier actions + explicit data gaps and not-evaluable checks.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check confirms: every finding has cited evidence, the severity counts and
readiness disposition tie out deterministically, no lending-decision / closure / filing /
waiver language is present, the standing disclaimer is included, and certifier actions are
listed whenever the package is not Complete. **Fail closed** on any miss.

## Human approval
`required`: a human certifier must review the assessment and make the certification /
clear-to-close / condition-waiver decision. The skill never certifies, waives, closes,
funds, or writes the system of record; it never issues a credit decision or adverse action.
No approval is needed for the reviewer's own read of the assessment.

## Failure handling
- **Missing checklist or unknown product/jurisdiction** → stop; the required-document set is
  undefined. Do not guess a checklist.
- **Ambiguous loan identity** → stop and confirm; never assess the wrong file.
- **Document present but effective_date missing** where a validity window applies → report
  the item as a **data gap / not-evaluable**, never as "valid".
- **Stale or conflicting sources** → cite both; do not silently pick one.
- **Tool timeout** → return the findings computed so far with a clear "incomplete" flag; do
  not imply the package is complete because the scan did not finish.

## Output contract
1. **Summary** — loan (masked as needed), package type, jurisdiction, `as_of`, severity
   counts, readiness disposition.
2. **Findings** — per finding: id, category, severity, plain-language summary, and cited
   evidence (document / checklist item / condition).
3. **Certifier actions** — the blocker and exception items the human must resolve or
   adjudicate before certification.
4. **Data gaps / not-evaluable checks.**
5. **Machine-readable** — findings + counts + `assessment_id` for downstream skills.
6. **Standing disclaimer** — "Completeness findings and cited evidence only; this is not a
   lending decision or package certification, and no loan action has been taken. Human review
   and certification are required before the package proceeds."
See [references/controls.md](references/controls.md).

## Privacy and records
Customer NPI/PII. Mask account/loan numbers to last 4 where displayed. Minimize customer
data in the output to what evidences a finding (do not echo full income or asset documents).
Retain the assessment + citations + checklist version per records policy; log the read and
the human certification event. Never exfiltrate customer or collateral documents.

## Gotchas
- **A finding is not a decision.** Blockers justify "not ready for certification", never a
  credit decision, a clear-to-close, or an adverse action — those are the human's.
- **Expiration is measured to the certification date**, not today; a package assessed for a
  future closing may show items valid now that expire by `as_of`. Use the package's `as_of`.
- **Checklist applicability is jurisdiction-driven**; a document required in one state is not
  in another. Only items whose `jurisdictions` include `ALL` or the package jurisdiction are
  evaluated — record which.
- **Consistency needs normalized entities**: "Jordan A Rivera" vs "Jordan Rivera" is an
  Exception to adjudicate, not proof of error; surface it, do not resolve it silently.
- **A cleared condition is the system's assertion, not proof**; if a condition is marked
  waived, flag it for the certifier to confirm the waiver authority — the skill never waives.
- **Do not tune the checklist to the file**; required items and validity windows come from
  the versioned config, not from what seems reasonable for this loan.
