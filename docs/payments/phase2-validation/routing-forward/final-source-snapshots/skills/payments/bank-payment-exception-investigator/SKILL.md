---
name: bank-payment-exception-investigator
description: >-
  Assemble cited bank-payment exception evidence, chronology, local case references, ownership gaps, and conditional recommendations from normalized ISO 20022 messages. Use for rejected, returned, or recalled bank payments. Read-only casework; native ACH and merchant-funding adapters, case persistence, decisions, and money movement are not implemented.
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
  aws-fsi-primary-user: "Payments investigations / operations analyst"
  aws-fsi-version: "0.2.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Bank Payment Exception Investigator

## Purpose and outcome
Prepare a bank-payment investigation package for a human case owner. The package preserves supplied identifiers and parties, assembles a chronology, records evidence gaps and finality uncertainty, and gives conditional next-step recommendations. Copying party data does not verify identity or account ownership.

## Inputs and prerequisites
Supply `scope: bank-payment`, `message_format: iso20022-normalized`, versioned configuration, `as_of`, optional open-case references, and `exceptions`. Each exception identifies its scheme, payment identifiers, amount/currency, and cited messages with timezone-aware timestamps. See [source-map.md](references/source-map.md).

The shipped adapter handles normalized ISO messages only. Native Nacha records, card chargebacks, merchant funding holds, and raw XML are outside its implemented scope. Scheme names do not make those adapters available.

## Workflow
1. Validate the input: `python3 -B scripts/validate_input.py exceptions.json`.
2. Build source-linked casework: `python3 -B scripts/calculate_or_transform.py exceptions.json`.
3. Preserve chronology and contradictory evidence. A recall requests action; it does not prove recovered funds. A reject does not prove that no other attempt settled.
4. Check the lead owner. Supplied case IDs are retained; generated `PEI-...` identifiers are explicitly local-only, not newly persisted cases. Missing ownership is `assignment-required`.
5. Make a repair/return/recall recommendation only when cited scheme eligibility, assessment owner/time, operation scope, window validity, and current finality are supplied. Repair also requires a confirmed defect and verified replacement. Missing evidence yields an information request; it never becomes inferred consent or an automatic rejection.
6. Validate the output: `python3 -B scripts/validate_output.py investigation.json`. The validator recomputes from the complete source request and separately checks the no-action boundary.

## Outputs and authority
The package carries source lineage, local/supplied case identity, owner status, priority rationale, evidence bundle, finality note, and a recommendation requiring human adjudication. Priority is illustrative triage using calendar-day aging; it is not an SLA clock. Amount scoring applies only in the configured threshold currency, with no implicit FX conversion.

`RR04` alone is a regulatory reason, not a sanctions determination. An explicit sanctions hold routes to sanctions adjudication; fraud indicators route to fraud casework. The skill never closes a case, communicates with counterparties, submits a response, persists a case, or moves money.

## Routing
Use [handoffs.md](references/handoffs.md). Direct entry is valid when case evidence already exists. A confirmed field defect can support `payment-repair-planner`, which only drafts a plan. Merchant funding/cash breaks belong to settlement reconciliation and merchant-risk review, not this bank exception package. No executor is shipped here.

## Supporting resources and checks
[domain-rules.md](references/domain-rules.md) describes disposition gates; [controls.md](references/controls.md) describes provenance and ownership; [payment-contract.md](references/payment-contract.md) defines shared monetary/evidence/handoff conventions. Run `python3 -B scripts/regression_tests.py`; executable evidence does not establish live connector or real-model readiness.
