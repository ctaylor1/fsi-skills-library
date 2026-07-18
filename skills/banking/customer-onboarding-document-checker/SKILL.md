---
name: customer-onboarding-document-checker
description: >-
  Check a customer-onboarding package for completeness before human approval: confirm every
  required document is present, unexpired, legible, and signed; cross-check identity fields
  (legal name, date of birth, address, TIN) across the application and supporting documents;
  and surface unresolved exceptions — each finding cited to its source. Use when an
  onboarding specialist, branch, or operations associate asks "is this onboarding package
  complete", "what documents are missing", "are these IDs expired or unsigned", "do the
  customer details match across documents", or needs a review-ready gap list before
  certifying a new account. This skill reports completeness gaps and a deterministic
  readiness status; it NEVER approves onboarding, verifies identity, makes a
  KYC/CIP/sanctions/PEP determination, waives a required document, or opens an account —
  those are human/authorized-system actions.
license: MIT
compatibility: Amazon Quick Desktop; requires document-intelligence, core-banking/onboarding-case, CRM, loan-origination/servicing, product-terms, and approved-calculation MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Banking"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 2 - analytical production"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Banking product & credit operations"
  aws-fsi-primary-user: "Onboarding specialist / branch or operations associate"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Customer Onboarding Document Checker

## Purpose and outcome
Given a customer-onboarding package, run a set of **explainable completeness checks** against
the configured required-document checklist, attach cited evidence to each fired finding, and
produce a review-ready **gap report** with a deterministic **readiness status**. A successful
output lets an onboarding specialist see exactly what is missing, expired, unsigned,
inconsistent, or unresolved — and remediate — before a human certifies the package. The
approval, the identity verification, and any account action remain human.

## Use when
- "Is this onboarding package complete / ready for review?"
- "What documents are missing or expired?"
- "Is the ID unsigned or the tax form unsigned?"
- "Do the name / date of birth / address match across the application and the documents?"
- A specialist needs a consistent, cited gap list to attach to an onboarding case.

## Do not use
- The user wants an **onboarding approval**, **identity verification**, or a **KYC/CIP/CDD**
  decision → out of scope. Report completeness and route to a human and the compliance
  skills. Substantive customer/beneficial-owner screening → `kyc-customer-due-diligence-screener`;
  higher-risk evidence assembly → `enhanced-due-diligence-packager`; ownership mapping →
  `beneficial-ownership-verifier`; customer risk rating → `customer-risk-rating-reviewer`.
- An **open watchlist/sanctions match** needs adjudication → `sanctions-match-adjudicator`
  (authorized reviewer).
- The package is actually a **lending application or closing package**, not deposit
  onboarding → `credit-application-packager` or `loan-package-completeness-checker`.
- **Merchant/business payments onboarding risk review** → `merchant-onboarding-risk-reviewer`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a completeness gap
report with a durable `checklist_id`; downstream screening/verification/packaging skills
consume it. It must not duplicate their determination, verification, or approval steps.

## Inputs and prerequisites
- **Package identifier** and the applicant record (legal name, DOB, address, TIN last 4).
- **Document set** for the package: each document with `type`, `status`
  (`provided`/`missing`/`illegible`), `issue_date`, `expiration_date`, `signature_present`,
  extracted `fields`, and a `source_ref`. Schema: [scripts/validate_input.py](scripts/validate_input.py).
- The **required-document checklist** and thresholds for the customer type, product, and
  jurisdiction (versioned config; see [references/domain-rules.md](references/domain-rules.md)).
- Read access to document-intelligence and the onboarding case; open **exceptions** list.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The imaged/extracted **document**
is evidence of what was collected; the **onboarding case** is the record for the applicant
and exceptions; the versioned **config** supplies the checklist. Cite every finding to a
document, field, config requirement, or exception. If an extracted field and the applicant
record conflict, cite both and raise a `data_inconsistency` finding — never reconcile
silently.

## Workflow
1. **Scope & validate** — confirm the package, customer type, product, jurisdiction, and
   `as_of`; load the document set, applicant record, exceptions, and config; run
   `validate_input`.
2. **Run checks (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to evaluate the
   configured checks (missing required doc, expired / expiring-soon, missing signature,
   illegible, stale, data inconsistency on key vs. non-key fields, unresolved exception).
   Each fired check returns its reason and the evidence rows behind it. Checks are
   **explainable**, not a black-box score.
3. **Assemble evidence** — for each fired check, attach the specific document(s), field
   value(s), config requirement, or exception, with citations.
4. **Map readiness** — map the fired findings to a readiness band (Ready /
   Ready-with-advisories / Not-ready) per the deterministic, documented mapping. This is a
   completeness state for a human, explicitly **not** an approval or identity verification.
5. **Write the report** — plain-language finding per check + the evidence + the readiness
   status + a remediation action per finding, and the handoffs for substantive screening.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check confirms: every fired check has evidence + citation, no
approval/verification/determination/action language is present, the readiness status maps
deterministically from the findings, the standing disclaimer is present, and remediation
prompts are included. Fail closed on any miss.

## Human approval
`external-delivery`: human review required before the gap report is sent to the
customer/applicant or written to the onboarding case/system of record. No approval is needed
for the specialist's own read. The skill never approves onboarding or takes an account
action.

## Failure handling
- **Missing expiration/issue dates** on an expiry- or age-checked doc → report that check as
  not evaluable for that document; do not assume it is valid.
- **No extracted fields** on a document → data-consistency not evaluable for that document;
  state the gap.
- **Ambiguous package/identity** → stop and confirm; never check the wrong package.
- **Config/checklist unavailable** → do not guess the requirements; state that the checklist
  could not be loaded and fail closed.
- **Stale/conflicting sources** (document vs. applicant record) → cite both; raise a
  `data_inconsistency` finding; do not resolve silently.
- **Tool timeout** → return the checks computed so far with a clear "incomplete" flag; do not
  imply the package is complete.

## Output contract
1. **Summary** — package (masked), customer type/product/jurisdiction, `as_of`, blocking and
   advisory counts, readiness status.
2. **Findings** — per fired check: name, plain-language reason, severity, evidence rows
   (cited), and the remediation action.
3. **Not-evaluable checks** — where dates/fields/config were missing.
4. **Handoffs** — the substantive screening/verification skills to route to next.
5. **Machine-readable** — checks + evidence + `checklist_id` for downstream skills.
6. **Standing disclaimer** — "Completeness check only; not an onboarding approval, identity
   verification, or KYC/CIP determination. No account has been opened."
See [references/controls.md](references/controls.md).

## Privacy and records
Customer NPI/PII. Mask ID/TIN/account numbers to last 4. Minimize customer data in output to
what evidences a finding. Retain the checklist result + citations + `config_version` per
records policy; log the read and any external-delivery approval. Never exfiltrate customer
data.

## Gotchas
- **Complete is not approved.** "Ready" means the documents are present, current, signed, and
  consistent — it is never an onboarding approval, an identity verification, or a KYC/CIP
  pass. The human certifies; the compliance skills screen.
- **A mismatch is not fraud.** `data_inconsistency` flags a field to reconcile with the
  customer (e.g., a middle initial or maiden name); describe it factually, never as intent.
- **Do not waive.** Waiving a required document, signature, or exception is an approval
  action reserved for an authorized human — the skill flags, it does not waive.
- **Checklist is configuration.** Requirements come from the versioned per-jurisdiction /
  per-product config, not from guessing what "should" be needed for this customer.
- **Expiry is vs. `as_of`.** Expiration and staleness are judged against the stated package
  date; a document valid today may be expired for a back-dated package.
- **Open exceptions block readiness.** An unresolved watchlist/screening exception keeps the
  package Not-ready and routes to `sanctions-match-adjudicator` — this skill does not
  adjudicate it.
