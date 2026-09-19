---
name: payment-fraud-and-scam-investigator
description: >-
  Build payment-fraud and scam investigation evidence from supplied case records, including APP deception and BEC-related payments. Retain payment-case ownership; request a cyber email subinvestigation only when BEC email evidence exists. Produce chronology, illustrative risk score, evidence gaps and human-review recommendations; no fraud decision or money movement.
license: MIT
compatibility: Python 3 standard library; offline JSON input/output. Production source integrations, scheduling, case persistence and external actions are not implemented.
metadata:
  aws-fsi-category: "Payments"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Investigate & casework"
  aws-fsi-agent-pattern: "Case agent + evidence bundle"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII; cardholder data)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Payments operations & risk"
  aws-fsi-primary-user: "Fraud investigator / payments risk analyst"
  aws-fsi-version: "0.2.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Payment Fraud and Scam Investigator

## Purpose and outcome
Own the payment investigation for unauthorized transactions and authorized payments induced by deception. Package supplied customer, device, identity, behavior, transaction, beneficiary and network evidence. The score is illustrative and uncalibrated, not a fraud determination. Local derived case IDs are stable references, not proof a case was persisted.

## Inputs and prerequisites
Versioned configuration and cases with alert/case IDs, masked parties, channel, amount/currency, opened time, transactions/timeline, evidence pillars and source references. Scam flags include `app_scam_reported` and `bec_indicator`; `scam_evidence` records authorization evidence, victim account, beneficiary evidence, recovery status and reimbursement profile. `email_evidence_ref` is needed for a BEC email consultation. Separate sanctions/adverse-media flags are preferred; the legacy combined flag remains unresolved sanctions-specialist review.

## Workflow
1. Validate supplied identifiers, sources, evidence gaps and score configuration.
2. Build a chronology ordered by actual offset-aware timestamps, masked party references and linked evidence. Do not claim entity resolution or source retrieval occurred.
3. Calculate the supplied-signal score and report its configured thresholds and limitations.
4. Retain reported APP/BEC scams for human scam investigation regardless of low technical-risk scores. Surface authorization versus deception, victim/beneficiary evidence, recovery status and applicable reimbursement review. No low-score release inference for a reported scam.
5. If BEC and email evidence are supplied, add `phishing-and-bec-investigator` as a bounded email consultation returning to this payment case. Non-email APP scams remain here.
6. Consult sanctions, adverse-media and AML specialists for their determinations while preserving payment case ownership.
7. Produce recommendation and unresolved needs; adjudication, account actions, recovery execution and customer commitments require the responsible human workflow.

## Output contract
Case owner, supplied or local-derived case reference, cited chronology, masked parties, score/band/basis, evidence bundle, scam evidence gaps, bounded consultation requests and recommendation. APP/BEC currently yields `needs-evidence` for human scam review even when technical fields are populated. This is intentional triage, not autonomous scam adjudication.

## Adjacent-skill handoffs
`instant-payment-risk-monitor` can supply alerts. `phishing-and-bec-investigator` examines email artifacts only; return evidence here. Sanctions match → `sanctions-match-adjudicator`; adverse media → `adverse-media-investigator`; suspicious patterns → AML triage/investigation. Keep restricted financial-crime evidence appropriately scoped. Issuer statutory redress → `issuer-payment-dispute-reviewer`; merchant/acquirer dispute response → `merchant-chargeback-response-packager`; operational repair planning → `payment-repair-planner`. A handoff is a review request, not execution authority.
Read [handoffs](references/handoffs.md) before transferring evidence.

## Source hierarchy and rules
Read [source-map](references/source-map.md) for authority and access boundaries, [domain-rules](references/domain-rules.md) for calculations and status meaning, and the [payments contract](references/payment-contract.md) for evidence, time, money and handoff semantics.

## Human approval and controls
This package prepares analysis or drafts only. It grants no execution authority. Human review requirements concern downstream regulated decisions or external actions, not running these offline checks. Use [controls](references/controls.md) for limits; protect customer and cardholder data, use masked identifiers, and retain source/version context with the review record.

## Validation and failure handling
Run `python3 -B scripts/validate_input.py INPUT.json`, then `python3 -B scripts/calculate_or_transform.py INPUT.json`, then `python3 -B scripts/validate_output.py OUTPUT.json`. Run `python3 -B scripts/test_regressions.py` for changed behaviors. Structural errors stop the CLI. Missing substantive evidence or rule applicability stays explicitly unresolved; do not repair it by inventing inputs. The fixtures are synthetic. Passing software checks does not establish professional acceptance or deployed-agent quality.
