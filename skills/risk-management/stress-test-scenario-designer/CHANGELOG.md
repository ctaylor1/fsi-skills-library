# Changelog — stress-test-scenario-designer

## [0.1.0] — 2026-07-18
Initial authoring in the FSI Skills Library (baseline status: `new`). R3 regulated
decision-support domain workflow: designs and evidences candidate stress scenarios for human
adjudication; it never adopts, decides, sets a limit, certifies a model, or files.

- **Scope:** severity ladder (baseline / adverse / severely-adverse), risk-factor shocks,
  transmission channels, assumptions, management actions, and reverse-stress thresholds, with
  explainable severity, coverage, plausibility, and distance-to-breach evidence. Read-only.
- **Deterministic engine (`scripts/calculate_or_transform.py`):** shock vectors, impact-
  weighted severity, transparent linear constraint projection + distance-to-breach, reverse-
  stress scaling multiple, coverage/plausibility/monotonicity flags, and a deterministic
  readiness band (documented in `references/domain-rules.md`).
- **Controls:** R3; hard boundary against scenario adoption/approval, capital/liquidity
  adequacy or pass/fail determinations, limit/trigger setting, model certification, and
  regulatory filing; versioned-config bands and betas only; `required` human adjudication.
- **Scripts:** `validate_input` (schema, factor/constraint/scenario checks, calibration
  warnings), the engine, and `validate_output` (structural completeness, coverage,
  reverse-stress presence, deterministic readiness tie-out, decision/adoption/filing/advice
  language screen, disclaimer).
- **Evaluations:** trigger/routing (liquidity/market/credit/model-validation handoffs), golden
  Ready-for-review case, non-monotonic edge, deterministic script checks, no-decision safety +
  injection, and adjudication authorization.
- **Handoffs:** downstream to `liquidity-risk-scenario-analyzer`, `market-risk-limit-monitor`,
  `credit-risk-portfolio-analyzer`, `enterprise-risk-assessment-builder`,
  `model-validation-assistant`, `model-risk-documenter`, and
  `operational-resilience-scenario-tester`; adoption/filing routed to human functions.

### Pending before release
- Domain SME (enterprise/capital/liquidity risk) + control-owner blind review; independent
  model-risk review of the transmission betas.
- Confirm the versioned scenario-config source (bands, plausibility floors, betas, limits) and
  its owner.
- Wire read-only MCP integrations (stress-config, risk register, finance/operational data,
  scenario library) at deployment.
