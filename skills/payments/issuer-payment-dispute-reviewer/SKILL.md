---
name: issuer-payment-dispute-reviewer
description: >-
  Prepare issuer-side customer payment-error and dispute review records with statutory obligations separated from scheme recovery. Requires a supplied applicable legal profile and named cited clocks; missing profiles remain unresolved. Merchant/acquirer representment routes to merchant-chargeback-response-packager. No adjudication, credit, filing or closure.
license: MIT
compatibility: Python 3 standard library; offline JSON input/output. Production source integrations, scheduling, case persistence and external actions are not implemented.
metadata:
  aws-fsi-category: "Payments"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Draft & package"
  aws-fsi-agent-pattern: "Case agent + evidence bundle"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII; cardholder data)"
  aws-fsi-jurisdictions: "US, euro area and UK initial reference profiles; case and institutional review required"
  aws-fsi-owner: "Payments operations & risk"
  aws-fsi-primary-user: "Issuer / acquirer disputes analyst"
  aws-fsi-version: "0.2.1"
  aws-fsi-recertification-date: "2027-09-18"
---

# Issuer Payment Dispute Reviewer

## Purpose and outcome
Own the issuer customer-error review checklist and preserve applicable statutory duties independently of scheme recovery. The package checks supplied profile/clock/evidence structure. It does not determine legal applicability, compute a complete legal rulebook or recommend defending against the customer.

## Inputs and prerequisites
`processing_date`, cases with `case_id`, `role`, jurisdiction, rail, product, transaction identity, explicit amount/currency and source reference. Issuer cases supply a shared-contract `statutory_profile`, `statutory_clocks`, evidence and `statutory_action_reviews`. Optional scheme profile/clocks are separate. See [domain-rules.md](references/domain-rules.md) for the exact additional fields.

## Workflow
1. Route merchant/acquirer response work to the merchant packager; keep issuer cases here.
2. Validate transaction identity and amount/currency.
3. Check the declared active legal profile covers issuer, jurisdiction, product and rail and is within effective/review dates. Absent or stale/proposed profiles remain `legal-profile-unresolved`.
4. Check every named statutory clock has its legal source, trigger event/date/evidence, explicit due date and day basis. Business-day clocks need a named calendar/cutoff reference. Do not substitute scheme clocks.
5. Surface overdue statutory clocks for urgent issuer review without denying rights or closing the case. Check supplied review references for required provisional-credit applicability and customer-notice tasks.
6. Request fraud/scam consultation if needed while retaining the issuer servicing case and its clocks.
7. Produce a draft checklist for the authorized issuer reviewer; the reviewer determines duties, outcomes, notices and credits.

## Output contract
`statutory_review` and `scheme_review` remain separate, with named clocks and citations. Dispositions are `draft-ready-for-review`, `needs-data`, `legal-profile-unresolved`, `deadline-review-required`, or `route-specialist`. Draft-ready means supplied checklist fields are available for review, not that legal compliance or evidence sufficiency is established. `authorized_submission` remains false.

## Adjacent-skill handoffs
Merchant/acquirer representment → `merchant-chargeback-response-packager`. Fraud/scam investigations are consultations to `payment-fraud-and-scam-investigator`, returning evidence without extinguishing issuer deadlines. Payment exceptions → `bank-payment-exception-investigator`; reconciliation → `payment-transaction-reconciler` / `payment-settlement-reconciler`. Human issuer personnel own adjudication, provisional/final credit, notices, filing and closure.
Read [handoffs](references/handoffs.md) before transferring evidence.

## Source hierarchy and rules
Read [source-map](references/source-map.md) for authority and access boundaries, [domain-rules](references/domain-rules.md) for calculations and status meaning, and the [payments contract](references/payment-contract.md) for evidence, time, money and handoff semantics.

## Human approval and controls
This package prepares analysis or drafts only. It grants no execution authority. Human review requirements concern downstream regulated decisions or external actions, not running these offline checks. Use [controls](references/controls.md) for limits; protect customer and cardholder data, use masked identifiers, and retain source/version context with the review record.

## Validation and failure handling
Run `python3 -B scripts/validate_input.py INPUT.json`, then `python3 -B scripts/calculate_or_transform.py INPUT.json`, then `python3 -B scripts/validate_output.py OUTPUT.json`. Run `python3 -B scripts/test_regressions.py` for changed behaviors. Structural errors stop the CLI. Missing substantive evidence or rule applicability stays explicitly unresolved; do not repair it by inventing inputs. The fixtures are synthetic. Passing software checks does not establish professional acceptance or deployed-agent quality.

## Source-backed profile preparation

Read [references/profile-preparation.md](references/profile-preparation.md) for the
initial U.S., euro-area and U.K. consumer-error profiles and Visa stage orientation.
Run `python scripts/prepare_profile.py INPUT.json` to prepare a case-scoped profile
from a supplied specialist review. It does not calculate deadlines, authenticate
reviewers or replace native input/output validation. Public scheme stage guidance
cannot become an active licensed rule pack.
