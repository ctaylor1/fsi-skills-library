# Changelog — credit-risk-portfolio-analyzer

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** transparent credit-portfolio metrics + limit/threshold exceptions + cited
  evidence + a suggested review disposition. Read-only; R3 decision-support with mandatory
  human adjudication. No credit decision, allowance/reserve, limit action, closure, or filing.
- **Metrics (deterministic):** quality distribution and weighted-average PD/LGD, expected
  loss (`PD×LGD×EAD`), delinquency DPD buckets, single-name/sector/geography concentration
  with HHI, collateral/LTV, rating migration (downgrade rate / net notch), vintage cohorts,
  and stress-scenario impact — each explainable and evidenced (see
  `scripts/calculate_or_transform.py`).
- **Controls:** R3; hard boundary against autonomous credit decisions, allowance/reserve
  determinations, limit-breach disposition/waiver, case closure, filing, and system-of-record
  writes; versioned limits/scenario config only; PD/LGD consumed as governed model outputs;
  `required` human approval.
- **Scripts:** `validate_input` (portfolio schema, evaluability warnings), the metrics/
  exception engine, and `validate_output` (evidence/citation completeness, deterministic
  disposition tie-out, prohibited decision/closure/filing screen, disclaimer, adjudication
  note). Each carries a `--selftest` over a bundled fixture.
- **Evaluations:** trigger/routing, golden Elevated case, thin-portfolio edge, deterministic
  script checks, prohibited-decision safety fixture (fails closed) + injection, and
  human-adjudication authorization.
- **Handoffs:** downstream to `stress-test-scenario-designer`, `concentration-risk-monitor`,
  `key-risk-indicator-monitor`, `credit-memo-drafter`, `enterprise-risk-assessment-builder`,
  and `covenant-compliance-monitor`; model-governance boundary to `model-validation-assistant`
  and `model-risk-documenter`.

### Pending before release
- Domain SME (credit risk) + control-owner blind review; fairness review of risk drivers.
- Confirm the versioned limits/appetite config and scenario library sources and their owners.
- Confirm PD/LGD model-output contract and version stamping with model risk management.
- Wire read-only MCP integrations (loan tape, rating store, collateral, limits, scenarios) at
  deployment.
