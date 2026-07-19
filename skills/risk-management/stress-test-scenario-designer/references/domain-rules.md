# Domain Rules — stress-test-scenario-designer

How a candidate stress-scenario set is structured, calibrated, projected, and scored for
review-readiness. Every threshold, band, and sensitivity is **configuration** (versioned,
owned by the enterprise-risk / model-risk functions), not a hard-coded judgment, and none
of it constitutes an approval. Orientation references: the firm's stress-testing and ICAAP/
ILAAP standards and the applicable supervisory stress-test framework (e.g., CCAR/DFAST) take
precedence over anything here. The 2026 FINRA report is an orientation reference only.

## Scenario object (design contract)

Each scenario carries: `name`, `severity` (`baseline` | `adverse` | `severely_adverse`),
a set of `variables` (risk-factor `value`s), `transmission_channels` (how factors flow to
each binding constraint), `assumptions`, and `management_actions` (required on every stress
scenario). A shock is `value - baseline_value` for the factor, measured against the
`baseline` scenario's values.

## Deterministic computations (see scripts/calculate_or_transform.py)

| Computation | Rule |
| ----------- | ---- |
| **Shock vector** | Per factor, `shock = scenario_value - baseline_value`. |
| **Severity score** | Impact-weighted L1 size: `sum over binding constraints of |impact_sum|`. Explainable, not an opaque index. |
| **Constraint projection** | Transparent linear transmission: `stressed = starting_value + sum(beta[metric][factor] * shock[factor])`. Betas are versioned config. |
| **Distance to breach** | `min` constraint: `stressed - limit` (positive = headroom above the floor). `max` constraint: `limit - stressed`. `breached` is reported factually as a projection, never as a determination. |
| **Reverse-stress multiple** | Scalar `λ = (limit - starting) / impact_sum` for the target constraint under the target scenario. `λ < 1`: the scenario already reaches the limit at `λ×` severity. `λ ≥ 1`: the shock vector must be amplified `λ×` to reach the limit. `λ ≤ 0` or zero impact: reported "not reachable by scaling this scenario". |

## Severe-but-plausible calibration

Each factor declares a `plausible_max_shock` (an upper magnitude beyond which a shock is
flagged **implausibly severe**) and a `severe_min_shock` (a floor the `severely_adverse`
shock must meet, else it is flagged **insufficiently severe**). These bands come from the
firm's historical and expert-judgment calibration, not from this skill.

## Coverage rules

- Every binding constraint's transmission betas must resolve to a **defined** factor that is
  **present** in the scenario's variables (no dangling or missing driver).
- Every scenario factor should feed **at least one** binding constraint (no orphan variable
  with no transmission channel).
- Gaps are reported per scenario as `coverage_gaps`.

## Severity monotonicity

Across the ordered ladder `baseline < adverse < severely_adverse`, `severity_score` must be
strictly increasing. A non-monotonic ladder is a calibration error, not a ready design.

## Readiness band (deterministic, documented — NOT an approval)

| Band | Rule |
| ---- | ---- |
| **Ready-for-review** | No scenario has `components_missing`, no `coverage_gaps`, no `plausibility_flags`, and the ladder is monotonic. |
| **Not-ready** | Any of the above fails. |

`Ready-for-review` means the candidate set is **structurally complete and internally
consistent enough for a human reviewer to challenge** — it is a completeness/quality gate,
never a statement that the scenario is adopted, that capital/liquidity is adequate, or that
the firm passes.

## Hard boundaries (fail closed)

- Never **adopt/approve** a scenario, declare it the official/regulatory scenario, or state
  it will be **filed/submitted**.
- Never make a **capital or liquidity adequacy** determination, a pass/fail call, or a
  distribution/dividend decision.
- Never **set a binding limit** or the reverse-stress trigger as a system-of-record value;
  propose a candidate threshold with evidence only.
- Never **certify** the transmission model or its betas — model soundness is independent
  validation's call (route to `model-validation-assistant`).
- Describe projected breaches and distances **factually**; attribute all conclusions and
  adoption to the human risk committee / model risk / board.
