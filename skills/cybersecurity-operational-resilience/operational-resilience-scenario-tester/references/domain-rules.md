# Domain Rules — operational-resilience-scenario-tester

How the deterministic engine scores a severe-but-plausible scenario test and maps the result
set to a **suggested review disposition**. Thresholds and the rubric are configuration
(versioned, owned by the operational-resilience programme), not hard-coded judgments, and are
never tuned to make a service "pass". Orientation references: UK PRA/FCA operational
resilience (SS1/21, important business services and impact tolerances), EU DORA (digital
operational resilience testing), and the firm's resilience standard, which take precedence.

## Core concepts

- **Important business service (IBS):** a service whose disruption harms customers or market
  integrity. Each IBS carries an **impact tolerance** — the maximum tolerable disruption
  (default legs: `max_downtime_hours`, `max_data_loss_hours`).
- **Severe-but-plausible scenario:** a disruption that is both *severe* (meaningfully
  stresses the service) and *plausible* (could realistically occur). A scenario below either
  bar is a weaker test and is flagged, not silently accepted.
- **Dependency dimensions:** `people`, `process`, `technology`, `facilities`,
  `third_parties`, `data`. A test's coverage is measured against the dimensions the IBS
  actually depends on.

## Rubric flags (quality of the test, not a decision)

| Flag | Fires when |
| ---- | ---------- |
| `below_severe_threshold` | Scenario severity ranks below `min_severity_for_test` (default `severe`) |
| `below_plausibility_threshold` | Scenario plausibility ranks below `min_plausibility_for_test` (default `plausible`) |

## Impact-tolerance test (deterministic, factual)

For each leg (`downtime`, `data_loss`): compare the **observed** recovery metric to the IBS
**tolerance**.

- `outcome = within` if observed <= tolerance; `breach` if observed > tolerance;
  `not_evaluable` if the observed metric is missing.
- `margin_hours = tolerance - observed` (negative on a breach).
- Scenario `outcome` = `breach` if either leg breaches; `not_evaluable` if downtime is not
  evaluable; else `within`.
- `thin_margin` = a `within` scenario whose smallest leg margin is below
  `margin_buffer_hours` (default 1.0) — a within-tolerance result with little headroom.

This is an observed-vs-stated **fact** about one exercise. It is **not** a statement that the
service "is resilient", "is compliant", or "can remain within tolerance" going forward — that
firm-level conclusion is a human adjudication (see controls.md).

## Coverage

`declared_dimensions` = dependency dimensions the IBS actually has. `exercised_dimensions` =
those the scenario exercised. `missing_dimensions` = declared minus exercised.
`coverage_ratio = |exercised| / |declared|`. Missing dimensions are surfaced as gaps.

## Decision & recovery evidence

- Each response **decision** is complete only with `owner_role` + `timestamp` +
  `evidence_ref`. Incomplete decisions are `decision_gaps`.
- Each scenario with an evaluable outcome must carry >= 1 **recovery evidence** row with a
  citation; otherwise the recovery is unevidenced (a fail-closed error in `validate_output`).
- Each **lesson** becomes a `remediation_action` with an owner role and status
  `open_for_human_adjudication` — the skill records it; it does not close it.

## Disposition mapping (deterministic, documented)

Computed identically in `scripts/calculate_or_transform.py` and `scripts/validate_output.py`.

| Suggested band | Rule |
| -------------- | ---- |
| **Escalate** | Any scenario `outcome == breach`, OR any lesson of severity `high`/`severe`/`critical` |
| **Review** | No breach/high lesson, but any of: missing coverage dimension, a `medium` lesson, a `thin_margin` scenario, a rubric quality flag, a decision gap, or a `not_evaluable` scenario |
| **Informational** | All scenarios within tolerance, full coverage, complete decisions, only low-severity lessons |

The disposition is a **triage suggestion for a human reviewer / accountable owner**. It is
not a resilience determination, a self-assessment sign-off, or a regulatory outcome, and it
never triggers a filing or a system-of-record change.

## Hard boundaries (fail closed)

- Never assert the firm/service **is compliant**, **is resilient**, or **can/will remain
  within impact tolerance** — describe the observed test result and attribute the conclusion
  to the human adjudicator.
- Never **sign off** a self-assessment, **attest**, **file/submit** a regulatory report, or
  **close** a case/exercise/finding.
- Never tune the rubric or tolerances to produce a `within` result; use only the versioned
  config, and use the impact tolerance in force at `as_of`.
- Regulatory reporting and jurisdictional registers are a **separate workflow** (route to
  the `operational-resilience-reporter`); do not duplicate them here.
