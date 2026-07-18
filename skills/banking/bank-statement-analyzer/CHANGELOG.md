# Changelog — bank-statement-analyzer

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `existing-updated` relative to
the AWS baseline — stronger evidence traceability, tie-outs, confidence flags, and a
no-lending-decision / no-advice guardrail).

- **Scope:** source-linked statement spread — income, recurring obligations, cash-flow
  trends, and fees — plus factual anomaly flags with confidence. Read-only; no lending,
  affordability, or eligibility decision, no advice, no fraud determination.
- **Extraction (deterministic):** income (payroll/recurring credits), recurring obligations
  (stable-amount counterparties), cash flow with a balance tie-out, fees (word-boundary
  keyword match), and anomalies (negative-balance day, NSF/returned item, large one-off
  debit, duplicate transaction) — each evidenced and cited (see
  `scripts/calculate_or_transform.py`).
- **Controls:** R2; hard boundary against lending/credit/affordability/eligibility decisions,
  personalized financial advice, and fraud determinations; versioned-config thresholds only;
  confidence flags required; `external-delivery` approval.
- **Scripts:** `validate_input` (statement schema, data-quality warnings), extraction engine,
  `validate_output` (evidence/citation completeness, deterministic tie-outs, decision/advice
  language screen, standing disclaimer, confidence-flag presence).
- **Evaluations:** trigger/routing, golden statement case (4 anomalies, tie-out), missing-
  balance edge, deterministic script checks, no-decision safety + injection, external-delivery
  authorization.
- **Handoffs:** downstream to `loan-affordability-precheck`, `financial-spreading-assistant`,
  `cashflow-forecaster`, `fee-and-charge-reviewer`, `account-anomaly-screener`,
  `credit-application-packager` / `credit-memo-drafter`.

### Pending before release
- Domain SME (credit/deposit ops) + control-owner blind review; fairness review of
  categorization and anomaly heuristics.
- Confirm the versioned categorization/threshold config source and its owner.
- Wire read-only MCP integrations (statements, document intelligence, CRM, reference data,
  config) at deployment.
