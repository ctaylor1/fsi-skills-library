# Changelog — commercial-cash-management-advisor

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** explainable, source-linked treasury-service **fit recommendations** with cited
  evidence and per-service implementation questions, plus a suggested engagement-priority
  band. Read-only; no pricing, credit, investment, or enrollment decision.
- **Service-fit rules (deterministic):** excess-balance/earnings-credit, liquidity structure
  (ZBA/sweep/pooling), lockbox, remote deposit capture, merchant services,
  controlled disbursement/integrated payables, check Positive Pay, ACH debit block,
  FX/international, and an overdraft/liquidity **referral** — each explainable and evidenced
  (see `scripts/calculate_or_transform.py`).
- **Controls:** R2; hard boundary against binding product/pricing decisions, credit
  decisions/creditworthiness assertions, personalized investment advice, and
  open/enroll/change/price actions; versioned-config thresholds only; existing services are
  not re-recommended; `external-delivery` approval.
- **Scripts:** `validate_input` (cash-profile schema, evaluability warnings), fit engine with
  internal self-check, `validate_output` (evidence/citation + implementation-question
  completeness, deterministic priority tie-out, binding-decision/advice screen, disclaimer).
- **Evaluations:** trigger/routing, golden Priority-review case, thin-profile edge,
  deterministic script checks, no-decision safety + injection, external-delivery
  authorization.
- **Handoffs:** upstream `bank-statement-analyzer`, `cashflow-forecaster`,
  `customer-onboarding-document-checker`; downstream `fee-and-charge-reviewer`,
  `merchant-fee-optimizer`, `credit-application-packager`,
  `kyc-customer-due-diligence-screener`, `account-anomaly-screener`; human handoffs to the
  pricing desk, commercial-lending underwriter, licensed investment specialist, and treasury
  operations.

### Pending before release
- Domain SME (TM product) + control-owner blind review; conduct/fairness review of fit rules.
- Confirm the versioned threshold/priority config source and its owner.
- Wire read-only MCP integrations (core-banking balances/activity, CRM, product terms,
  config) at deployment.
