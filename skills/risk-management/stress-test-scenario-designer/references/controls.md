# Controls — stress-test-scenario-designer

- **Risk tier:** R3 — regulated / control decision support. **Action mode:** Read-only
  analysis.
- **Human approval:** `required` — mandatory human adjudication (risk committee / model risk
  / board) before any scenario is adopted, any threshold is set, any capital/liquidity
  decision is made, or anything is filed.

## Prohibited (fail closed)

- No **adoption/approval** of a scenario, no declaring it the official/regulatory scenario,
  no statement that results will be **filed or submitted** (CCAR/DFAST/ICAAP/ILAAP).
- No **capital or liquidity adequacy** determination, **pass/fail** call, or
  **distribution/dividend** decision.
- No **setting of a binding limit** or reverse-stress trigger as a system-of-record value —
  propose candidate thresholds with evidence only.
- No **certification** of the transmission model or betas (route to independent validation).
- No **personalized investment/trading advice** and no autonomous **system-of-record write**.
- No tuning of severity/plausibility bands per-run to force a desired outcome; use only the
  versioned config.

## Required output screens (`scripts/validate_output.py`)

- Every scenario has transmission channels + assumptions; every stress scenario has
  management actions; each impact has a numeric distance-to-breach.
- No scenario carries coverage gaps; reverse stress is present (scaling multiple or an
  explicit "not reachable" interpretation).
- `readiness_band` equals the deterministic mapping from the pack's structural, coverage,
  monotonicity, and plausibility flags.
- No decision/adoption/filing/advice language (regex screen: "is approved", "adopted as the
  official", "we will file/submit", "capital is adequate", "passes/fails the stress test",
  "board has approved", "set the limit", "certify the model", etc.).
- Standing disclaimer present: see the exact text in `scripts/calculate_or_transform.py`
  (`DISCLAIMER`).

## Segregation of duties

Design (this skill) is separated from **independent validation** of the model/betas
(`model-validation-assistant`), from **running** the downstream risk analytics
(`liquidity-risk-scenario-analyzer`, `market-risk-limit-monitor`,
`credit-risk-portfolio-analyzer`), and from **adoption** (risk committee / board). The skill
never performs more than one of these roles.

## Data classification, privacy, records

- **Confidential** (firm risk/finance data; typically no customer PII). Keep exposures and
  starting values at the aggregate level the design requires.
- Retain the design pack + `design_id` + `config_version` + starting-value as-of dates per
  records policy; log the read and the adjudication decision made by the human owner.

## Reproducibility

`design_id` binds the pack to the exact inputs, `config_version` (bands, plausibility, betas,
limits), and starting values; re-running with the same inputs and config reproduces the
severity scores, projections, reverse-stress multiple, and readiness band.
