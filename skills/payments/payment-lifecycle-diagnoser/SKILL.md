---
name: payment-lifecycle-diagnoser
description: >-
  Trace one payment across initiation, authorization, clearing, settlement, and reported failures using cited normalized events. Distinguish approval from settlement and route unresolved bank exceptions, card operations, fraud, or customer remediation. Read-only diagnosis; no payment actions or retry authorization.
license: MIT
compatibility: Python 3.10+; bundled standard-library scripts consume local JSON. No live MCP or payment-system adapters are implemented.
metadata:
  aws-fsi-category: "Payments"
  aws-fsi-skill-type: "Guidance or domain-expertise skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Domain workflow"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 1 - stabilize existing"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "existing-updated"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII; cardholder data)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Payments operations & risk"
  aws-fsi-primary-user: "Consumer / merchant / payments operations analyst"
  aws-fsi-version: "0.2.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Payment Lifecycle Diagnoser

## Purpose and outcome
Produce a cited lifecycle diagnosis for one payment, identifying observed states, unresolved gaps, and an appropriate owner. Authorization approval, clearing, settlement, funding, and posting are separate events. A successful diagnosis may conclude that the payment is still in progress or that the evidence is insufficient.

## Inputs and prerequisites
Supply normalized JSON with `payment_id`, `as_of`, `rail`, and ordered `legs` (`seq`, `stage`, `status`, `source_ref`; optional reason and timestamp). If an amount is supplied, currency must be explicit. See [source-map.md](references/source-map.md) for the adapter and evidence limits.

Bundled code meanings are representative examples, not an authoritative network code service. `wire` and `rtp` do not imply ISO 20022: supply `code_system: iso20022` when supported by the source. Unknown codes remain unknown. The reported source `codeset_version` does not cause this offline script to retrieve that version.

## Workflow
1. Validate inputs with `python3 -B scripts/validate_input.py trace.json`.
2. Build the diagnosis with `python3 -B scripts/calculate_or_transform.py trace.json`.
3. Inspect the cited trace and gaps. A card `00`/`APPROVED` is authorization, never proof of settlement. Pending is not automatically timeout. Completion statuses lacking payment-linked settlement evidence remain `settlement_reported`.
4. Validate the generated output with `python3 -B scripts/validate_output.py diagnosis.json`; explain the observed state and route using [handoffs.md](references/handoffs.md).

The output includes the source trace/hash, `diagnosis_id`, interpreted legs, evidence-backed root category, suggested route, cautions, and trace completeness. `retry_eligible` is always false in this adapter because scheme-specific retry authorization is not implemented. This does not determine whether a qualified operator could later authorize a retry.

## Scope and routing
- Bank-payment casework → `bank-payment-exception-investigator`; a format code alone is insufficient for a repair plan.
- Card operational ambiguity → `payment-operations-review`, a human operations destination, not a claimed installed skill.
- Normalized ISO field explanation → `iso-20022-message-interpreter`.
- Confirmed payment fraud indicators → `payment-fraud-and-scam-investigator`, without a fraud determination here.
- Aggregate authorization/decline analysis belongs to merchant performance analysis, not this single-payment trace.

Direct entry is allowed with sufficient evidence; no mandatory interpretation→diagnosis→casework pipeline exists. This skill never changes a payment or sends an external message.

## Controls and supporting resources
Use [domain-rules.md](references/domain-rules.md) for state and routing rules, [controls.md](references/controls.md) for source replay and action boundaries, and [payment-contract.md](references/payment-contract.md) for shared money/evidence/handoff conventions.

## Validation
`python3 -B scripts/regression_tests.py` checks meaningful lifecycle and validator behavior. `evals/evals.json` separates executable checks from conceptual routing/model cases. Passing software checks is not real-model quality certification.
