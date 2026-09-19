---
name: merchant-payment-cost-analyzer
description: Analyze observed merchant acceptance costs from a supplied settled-sale statement, separating interchange, assessments, processor charges and fixed fees. Use for fee decomposition and data gaps; does not infer qualification, forecast savings, choose a processor or change contracts.
license: MIT
compatibility: Python 3.10+ offline JSON analysis. Expected source-system integrations must be supplied by deployment; no connectors or actions bundled.
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
  aws-fsi-primary-user: "Merchant / payments finance analyst"
  aws-fsi-version: "0.2.0"
  aws-fsi-recertification-date: "2027-09-17"
---

# Merchant payment cost analysis

Establish statement period, merchant scope, currency and which components are actually present. Use [references/source-map.md](references/source-map.md) for the input contract. Run `python scripts/validate_input.py INPUT.json`, `python scripts/calculate_or_transform.py INPUT.json`, then `python scripts/validate_output.py OUTPUT.json`.

Explain observed fee components and their settled-volume denominator. A supplied breakdown is not proof that contract rates or interchange qualification were correct. Missing fixed fees leave total cost unknown; never replace them with zero. Retain missing data level rather than assuming Level 1. Currency conversion and counterfactual economics require separate evidence and are outside this bounded calculator.

Use [references/domain-rules.md](references/domain-rules.md) for calculation boundaries, [references/payment-contract.md](references/payment-contract.md) for money/evidence semantics and [references/handoffs.md](references/handoffs.md) for adjacent jobs. The former default benchmark savings engine is removed: assumed discounts and overlapping cohorts did not support a defensible combined savings figure. Expanded economics is later-phase work.

Human commercial decisions and external delivery remain outside this offline analysis. No connector is bundled. Run `python scripts/test_phase1.py`; see [evals/evals.json](evals/evals.json).
