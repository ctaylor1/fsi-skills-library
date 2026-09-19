---
name: payment-repair-planner
description: >-
  Draft an exact before/after field-correction and resubmission proposal for a confirmed held or rejected bank-payment exception. Bind original instruction, verified replacement, screening scope, policy, and required approval role. R3 offline planning only: no approval verification, execution, release, return, or guaranteed rollback.
license: MIT
compatibility: Python 3.10+; bundled standard-library scripts consume local JSON. No live MCP or payment-system adapters are implemented.
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
  aws-fsi-primary-user: "Payments investigations / repair team"
  aws-fsi-version: "0.2.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Payment Repair Planner

## Purpose and outcome
Produce a reviewable offline proposal for correcting a confirmed payment defect. The outcome is a source-bound plan with an exact before/after field change, scoped policy, pending approval, and blocked execution. It is never a corrected or successfully resubmitted payment.

## Use when
- A repair specialist has confirmed a beneficiary-data defect or missing remittance/purpose information and needs a precise plan for review.
- An investigator supplies sufficient original-instruction, replacement-value, screening, and policy evidence for a proposed correction.

Do not use this package to execute an approved plan, release a screening hold, initiate a return/refund, recover settled funds, or determine a sanctions match. Routine servicing and live execution require their own authorized workflow. Suspected defects without confirmation belong to `bank-payment-exception-investigator`.

## Inputs and prerequisites
The exact schema is documented in [source-map.md](references/source-map.md) and illustrated by `evals/files/case_example.json`. It includes:
- Case/payment identity and a cited confirmed exception.
- The original payment snapshot: entity, rail, amount/currency, held/rejected state, source/time, end-to-end identifier, and original fields.
- Proposed action, field, exact old/new values, and unchanged payment amount/currency.
- A cited, versioned policy defining entity, rail, currency, allowed fields/types, positive amount limit, required approver role, and effective interval.
- Cited screening disposition bound to the complete original snapshot and proposed correction, and independent replacement-value evidence.

Nonempty references are supplied evidence, not authenticated authority. The local hash detects content changes; it is not a signature, approval, or guarantee of truthful source data.

## Workflow
1. Validate: `python3 -B scripts/validate_input.py case.json`.
2. Build: `python3 -B scripts/calculate_or_transform.py case.json`. Invalid evidence yields a rejected, blocked plan with no steps; the command exits nonzero.
3. Review the proposed field correction and resubmission steps, exact-change object, unchanged-field hash, full source snapshot, policy, screening scope, and human role. Idempotency scope is a proposal for a future execution ledger; this script cannot prevent duplicates in an external system.
4. Validate the actual output: `python3 -B scripts/validate_output.py plan.json`. It recomputes from the source request and rejects all claimed approvals, tokens, or execution—even when the content has been rehashed.
5. Present the proposal for human review. No approval broker, message validator, bank connection, executor, audit writer, or rollback operation is implemented.

## Control boundary
The only supported actions are proposed field corrections for the three documented defect classes, followed by a proposed resubmission. A policy cannot expand the package catalog. A policy limit in one currency never authorizes another currency without an independently approved policy. A changed beneficiary instruction requires screening evidence bound to that exact proposal.

Settled/unknown-state payments cannot be repaired through this adapter. A recall or compensation can fail and is not rollback. Unknown submission outcomes require investigation, not automatic retry. Changing a plan invalidates its previous integrity identifier and requires fresh review in any future approved execution system.

## Resources and validation
Read [domain-rules.md](references/domain-rules.md), [controls.md](references/controls.md), and [handoffs.md](references/handoffs.md) for supported types, evidence limits, and downstream prerequisites. [payment-contract.md](references/payment-contract.md) supplies common money/evidence/handoff conventions.

Run `python3 -B scripts/regression_tests.py`. These tests establish offline software behavior only; they do not validate live approvals or payment execution.
