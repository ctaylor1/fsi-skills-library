---
name: iso-20022-message-interpreter
description: >-
  Explain a cited normalized JSON view of ISO 20022 messages, distinguish transaction and status-report profiles, check exact supplied totals and identifier shapes, and classify other families without fabricating payment fields. No raw XML parser, XSD or scheme validation, live code-set retrieval, or payment action is implemented.
license: MIT
compatibility: Python 3.10+; bundled standard-library scripts consume local JSON. No live MCP or payment-system adapters are implemented.
metadata:
  aws-fsi-category: "Payments"
  aws-fsi-skill-type: "Utility skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Explain & summarize"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 2 - analytical production"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII; cardholder data)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Payments operations & risk"
  aws-fsi-primary-user: "Payments operations / implementation analyst"
  aws-fsi-version: "0.2.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# ISO 20022 Message Interpreter

## Purpose and outcome
Explain what a supplied normalized ISO message reports, preserving missing information and source lineage. This package is a small offline adapter, not a complete ISO parser or a scheme certification engine.

## Implemented profiles
- **Normalized transactions:** `pain.001`, `pain.008`, `pacs.003/004/007/008/009`. The adapter requires transaction identifiers, amounts/currencies, and source references.
- **Normalized status reports:** `pain.002`, `pacs.002`. Transaction amounts may be absent; group-only status reports are supported. Missing amounts are unknown, never zero.
- **Classification only:** other families/messages, including account-reporting/cancellation/investigation `camt` and `admi.024`. Names such as `camt.110/111` can be recognized without claiming their business structures are implemented. A source reference is required; no synthetic transfer rows or balance totals are produced.

These are package input profiles, not assertions that every listed ISO schema has those same mandatory fields. A supplied message/version/usage-guideline label does not validate against that schema or retrieve its rulebook.

## Workflow
1. Obtain de-identified **normalized JSON** with source references. Raw XML needs a separately available, validated parser; do not claim this package parsed it.
2. Run `python3 -B scripts/validate_input.py message.json`.
3. Run `python3 -B scripts/calculate_or_transform.py message.json`.
4. Review the classification, limitations, source-linked findings, status meanings, and per-currency totals. Status interpretations are representative bundled meanings; unknown codes remain unmapped. Message completion statements alone do not establish legal finality.
5. Run `python3 -B scripts/validate_output.py interpretation.json`. It independently regenerates the interpretation from its source and rejects invented totals, schema-validation claims, or payment directives.

## Important distinctions
A group control sum can be an arithmetic sum across currencies; it is not a fungible cash total. The output labels that value `raw_control_sum` and reports economic totals by currency. Absent declared controls are `not_evaluated`, not balanced. Control checks use exact decimal values without an invented percentage tolerance.

BIC shape, IBAN check digit, and UETR shape checks do not verify bank existence, account ownership, beneficiary identity, or scheme acceptance. Legacy truncation/charset warnings require an explicit cited `mapping_profile`; they are not universal ISO restrictions.

## Boundaries and routing
Lifecycle traces → `payment-lifecycle-diagnoser`; bank exception casework → `bank-payment-exception-investigator`; confirmed field-repair proposals → `payment-repair-planner`. These are optional compositions, not mandatory stages. This skill never changes or sends a message, makes a fraud/sanctions determination, or grants permission to move funds.

Read [source-map.md](references/source-map.md) for schemas and source limits, [domain-rules.md](references/domain-rules.md) for profile semantics, [controls.md](references/controls.md) for validation, [handoffs.md](references/handoffs.md) for composition, and [payment-contract.md](references/payment-contract.md) for shared conventions. Run `python3 -B scripts/regression_tests.py`; software tests do not establish real-model or live-schema quality.
