# Changelog — loan-affordability-precheck

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `existing-updated` relative to the
AWS baseline — stronger reproducibility, stress testing, and no-credit-decision guardrails).

- **Scope:** indicative affordability estimate (amortized payment, front/back DTI, residual income)
  + indicative band + rate/income stress cases. Read-only; no credit decision, no adverse action, no
  commitment to lend.
- **Computation (deterministic):** fixed-rate amortization, front-end/back-end DTI, residual income,
  and a documented band mapping from versioned thresholds — each explainable and reproducible (see
  `scripts/calculate_or_transform.py` and `references/domain-rules.md`).
- **Controls:** R3 decision-support; hard boundary against credit approval/denial/pre-approval,
  qualification/eligibility findings, adverse-action decisions, commitments, and personalized
  borrowing advice; fair-lending input restriction; versioned-config thresholds only; `required`
  human underwriting before any decision.
- **Scripts:** `validate_input` (loan/income/obligations schema, evaluability warnings), the
  affordability engine, `validate_output` (payment tie-out, deterministic band tie-out per baseline
  and per stress scenario, rate+income stress coverage, credit-decision/advice language screen,
  disclaimer, assumptions).
- **Evaluations:** trigger/routing, golden "Approaching typical limits" mortgage case, thin-inputs
  edge, deterministic script checks, no-credit-decision safety + injection, human-adjudication
  authorization.
- **Handoffs:** upstream from `bank-statement-analyzer`, `financial-spreading-assistant`,
  `cashflow-forecaster`; downstream to `credit-application-packager`,
  `loan-package-completeness-checker`, `credit-memo-drafter`, and human underwriting.

### Pending before release
- Domain SME (credit policy) + control-owner blind review; fair-lending (ECOA/Reg B) review of inputs
  and band language.
- Confirm the versioned threshold/stress config source, its owner, and per-jurisdiction packs.
- Wire read-only MCP integrations (loan origination/servicing, core-banking, CRM, document
  intelligence, product-terms config, calculation service) at deployment.
