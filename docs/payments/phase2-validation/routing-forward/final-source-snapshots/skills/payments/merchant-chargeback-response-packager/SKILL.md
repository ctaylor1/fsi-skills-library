---
name: merchant-chargeback-response-packager
description: >-
  Draft merchant and acquirer chargeback responses from supplied, cited evidence and a current stage-specific scheme profile. Use for representment packaging and response evidence gaps; issuer statutory error resolution belongs to issuer-payment-dispute-reviewer. No filing, liability decision or outcome guarantee.
license: MIT
compatibility: Python 3 standard library; offline JSON input/output. Production source integrations, scheduling, case persistence and external actions are not implemented.
metadata:
  aws-fsi-category: "Payments"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Draft & package"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 1 - stabilize existing"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "existing-updated"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII; cardholder data)"
  aws-fsi-jurisdictions: "US, euro area and UK initial reference profiles; case and institutional review required"
  aws-fsi-owner: "Payments operations & risk"
  aws-fsi-primary-user: "Merchant or acquirer chargeback analyst"
  aws-fsi-version: "0.2.1"
  aws-fsi-recertification-date: "2027-09-18"
---

# Merchant Chargeback Response Packager

## Purpose and outcome
Prepare merchant or acquirer response drafts, including a cited rebuttal and exhibit index. A draft-ready result means structural packaging checks passed; it does not establish substantive evidence sufficiency, compelling-evidence eligibility or likely success.

## Inputs and prerequisites
`as_of_date`, `ruleset_version`, a shared-contract `rule_profile` plus `stage`, and a supplied `reason_code_catalog`. Each dispute carries merchant/acquirer `role`, `jurisdiction`, `stage`, identity/amount/currency, an explicit `response_deadline` with `deadline_source_ref`, typed exhibits and exhibit-linked narrative points. The catalog specifies network, title, category and required evidence groups. There are no built-in production network windows.

## Workflow
1. Validate explicit dates, finite amounts, currency, identifiers and exhibit references.
2. Check declared profile status, effective/review dates, jurisdiction, participant and response stage. Missing or incompatible profiles remain `needs-data`.
3. Compare the supplied cited due date with `as_of_date`; never calculate a universal 30/45-day window. An acquirer deadline can differ from a network deadline.
4. Check evidence-group presence and transaction identity. A reference establishes supplied evidence, not truth or legal sufficiency.
5. Assemble only supported narrative points. Prior undisputed transactions are candidates for specialist compelling-evidence review, never automatic eligibility.
6. Validate the draft and hand it to the authorized merchant/acquirer reviewer. Submission is outside this package.

## Output contract
Per-dispute role, status, rule/deadline basis, remaining calendar days, evidence-group presence, identity issues, narrative/exhibit index and draft. `packageable` means draft structure ready for review. Every pack includes a content-lineage hash, version and standing note; a hash provides no authentication.

## Adjacent-skill handoffs
Issuer customer error, unauthorized-transfer or billing-error review → `issuer-payment-dispute-reviewer`. Merchant and acquirer representment remain here. Fraud/scam evidence → `payment-fraud-and-scam-investigator`; scheme changes → `payment-scheme-change-tracker`; settlement/ledger breaks → `payment-settlement-reconciler` / `payment-transaction-reconciler`. A scheme-change alert is not itself a current operating rulebook.
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
