# Adjacent-Skill Handoffs — stress-test-scenario-designer

This skill produces a cited **candidate scenario-design pack** (`design_id`) and stops. It
does not run the downstream risk models, validate the model, or adopt/file anything. Every
name below is a catalog skill; where no skill fits, the handoff is to a human function.

## Downstream (route the reviewer to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `liquidity-risk-scenario-analyzer` | Run the designed scenario through cash-flow, funding, collateral, and survival-horizon analysis | `design_id` + scenario variables + management actions |
| `market-risk-limit-monitor` | Apply the scenario to positions and compute stress losses against VaR/ES limits | `design_id` + market-factor shocks |
| `credit-risk-portfolio-analyzer` | Project portfolio loss, migration, and delinquency under the scenario | `design_id` + credit-factor shocks |
| `enterprise-risk-assessment-builder` | Fold the scenario into an enterprise risk assessment linking risks, controls, and treatments | `design_id` + transmission channels |
| `model-validation-assistant` | Independently validate the transmission model and betas used to project the scenarios | `design_id` + impact model + assumptions |
| `model-risk-documenter` | Assemble controlled model/scenario documentation and validation-evidence packs | `design_id` + full design pack |
| `operational-resilience-scenario-tester` | The need is a **service-disruption / operational-resilience** severe-but-plausible test, not a financial-capital/liquidity scenario | scope + impact tolerances |

## Upstream (may feed or call this skill)

| Upstream skill | Contribution |
| -------------- | ------------ |
| `operational-risk-event-analyzer` | Loss/near-miss events that anchor scenario severity and drivers |
| `concentration-risk-monitor` | Concentrations that inform transmission channels and idiosyncratic overlays |
| `key-risk-indicator-monitor` | KRI thresholds that inform reverse-stress trigger candidates |

A scheduled monitor is **not** used here (`aws-fsi-scheduled-agent: no`); the skill is
interactive.

## Human / specialist handoffs (no catalog skill)

- **Adoption** of a scenario set, approval of a capital/liquidity plan, or a
  distribution/dividend decision → the **risk committee / model risk / board**. The skill
  never adopts, approves, or files.
- **Regulatory submission** (CCAR/DFAST/ICAAP/ILAAP) → the accountable **regulatory reporting
  / treasury** function.

## Duplicate-execution prevention

- This skill **designs and evidences** a candidate scenario; it must not run the downstream
  liquidity/market/credit analytics, validate the model, or reach an adoption/adequacy
  conclusion.
- Downstream skills reuse the `design_id` scenario definition rather than re-designing it.
