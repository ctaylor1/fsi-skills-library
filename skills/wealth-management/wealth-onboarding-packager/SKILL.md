---
name: wealth-onboarding-packager
description: >-
  Assemble a proposed wealth relationship and account onboarding evidence pack against an explicit firm checklist: engagement, registration, identity, authority, consent, documents and external screening outcomes. Use to identify readiness gaps for an authorized onboarding reviewer. Does not perform KYC or sanctions adjudication, open accounts, transfer assets or deliver client communications.
license: MIT
compatibility: Agent Skills compatible; Python 3.10+ standard library. Supplied JSON evidence only; production read-only connectors and approved firm policies must be configured separately.
metadata:
  aws-fsi-category: "Wealth Management"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 6 - wealth management P0"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US; explicit professional-capacity and firm-policy applicability required"
  aws-fsi-owner: "Wealth Management advisory & compliance"
  aws-fsi-primary-user: "Advisor / relationship manager / onboarding operations"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-09-16"
---

# Wealth Onboarding Packager

## Purpose and outcome
Prepare a reviewable relationship/account evidence package and a concrete gap list for an
advisor, relationship manager or onboarding operator. The job begins after proposed engagement
and account scope are known and ends at an authorized human review. It does not approve
relationship acceptance, perform specialist screening or open an account.

## Use when
- "Prepare this household's onboarding pack and show what is missing."
- "Check registration, ownership, authority, consent and documents for these proposed accounts."
- "Bring together the custodian/KYC/sanctions review outcomes for the onboarding reviewer."

## Do not use
- KYC/CDD investigation or rating: `kyc-customer-due-diligence-screener`.
- Sanctions-match adjudication: `sanctions-match-adjudicator` and the authorized specialist.
- Banking product documentation alone: `customer-onboarding-document-checker`.
- Household planning discovery, investment recommendations, asset transfers or account opening.

## Inputs and prerequisites
Use `wealth-p0-v1`: request ID, de-identified household, as-of, engagement capacity/jurisdiction
and dated source registry. Supply relationship scope, proposed accounts/registrations, party
identity/authority records, consent records, documents, external review outcomes and an
explicit versioned firm checklist. Every material record requires `source_ids`.
Read [references/source-map.md](references/source-map.md) for field semantics and
[references/domain-rules.md](references/domain-rules.md) for completeness logic.
The policy must explicitly state required/not-required external review applicability and its
rationale. Never impose one universal RIA, broker-dealer, trust or private-bank AML checklist.

## Source hierarchy
Engagement documents and proposed custodian registrations anchor scope. Identity, authority
and consent evidence remains attributed to its source. Firm compliance owns checklist and
legal applicability; authorized specialist outcomes remain external evidence, not this skill's
approval. Conflicts stay visible. Source dates and owner fields are supplied metadata, not
proof of truth, access authorization or institutional approval.

## Workflow
1. Confirm household, professional capacity, account scope and permission to use the evidence.
2. Run [scripts/validate_input.py](scripts/validate_input.py). Resolve structural errors;
   preserve unavailable documents, consents and review outcomes as explicit gaps.
3. Run [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to assemble
   account, document, consent and external-review registers and owner-assigned next steps.
4. Run [scripts/validate_output.py](scripts/validate_output.py); it verifies the envelope and
   recomputes the result from its input snapshot. Altered readiness or approval claims fail.
5. Hand the internal draft to the authorized onboarding reviewer with
   [assets/output-template.md](assets/output-template.md). See
   [references/handoffs.md](references/handoffs.md) for specialist boundaries.

## Validation loop
A complete supplied checklist produces `review-ready`, meaning ready for human review only.
Any incomplete/conflicted evidence produces `needs-data`; do not describe the relationship
as approved, compliant or ready to open. Execute [scripts/test_regressions.py](scripts/test_regressions.py)
for source/date, registration, authority, consent, external-review, tampering and no-action checks.
Behavior/routing scenarios in [evals/evals.json](evals/evals.json) require separate real-agent evaluation.

## Output contract
Envelope: artifact ID, full input digest, source/context registry, findings, status and immutable
review-required/no-action/not-delivered flags. Result: relationship/policy IDs, proposed account
register, supplied documents and consents, attributed external review outcomes, policy
applicability, gaps and next steps, standing disclaimer. `input_snapshot` permits re-verification.
It must contain only minimized structured evidence, not raw identity documents or client NPI.

## Human approval
Authorized onboarding/compliance personnel decide relationship/account acceptance and whether
legal prerequisites are met. Specialist review outcome evidence is not delegated authority to
open or activate an account. These scripts have no external operations, delivery or writes.

## Failure handling
Malformed identity, duplicate record IDs, invalid sources, unsupported jurisdiction or wrong
record types stop calculation. Missing domain evidence becomes `needs-data`. A missing or
mismatched firm policy cannot yield review-ready. Unknown or escalated specialist outcomes
remain outstanding; never clear a match. A timeout must retain incomplete coverage explicitly.

## Privacy and records
Minimize PII, use internal de-identified household/party/account references, and retain only
necessary status evidence and source references. The input snapshot inherits source access
restrictions. Separate restricted AML/SAR details from client-facing material. Retention and
adjudication logging are institutional responsibilities; this package does not implement them.

## Gotchas
Received documents are not verified identities; supplied owner completion is not this skill's
KYC determination. A trust or entity requires its own explicit registration checklist; the
individual-account fixture cannot be reused as one. Multiple conflicting copies are gaps,
not permission to choose whichever looks complete. The software is deterministic-test validated;
SME/compliance acceptance, production connectors and behavioral evaluation remain pending.
See [references/controls.md](references/controls.md).
