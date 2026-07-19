# Domain Rules — enterprise-risk-assessment-builder

Orientation references: COSO ERM and ISO 31000 risk-management principles, the firm's
enterprise risk-management policy, its risk taxonomy, and its board-approved risk appetite
statement. The firm's policy, taxonomy, scoring configuration, and appetite bands take
precedence and are **versioned contracts** (`config_version`, `template_version`).

## Inherent risk scoring (deterministic, documented)

Inherent risk is `likelihood (1-5) x impact (1-5)` on the firm's 5x5 scale, banded:

| Score (L x I) | Inherent band |
| ------------- | ------------- |
| 1–4 | Low |
| 5–9 | Moderate |
| 10–15 | High |
| 16–25 | Critical |

Likelihood and impact are inputs sourced from the risk register and sized with finance /
operational data; they are not invented by the skill.

## Control effectiveness and residual credit

Each linked control carries **design** and **operating** effectiveness:

| Effectiveness | Value |
| ------------- | ----- |
| Effective | 2 |
| Partially Effective | 1 |
| Ineffective | 0 |
| Not Tested | no credit (unproven) |

A control is **proven** only when both design and operating are tested (not `Not Tested`).
Residual credit is taken **only** for controls that are proven **and** carry an evidence
reference. For a risk, average the combined score (design + operating, 0–4) of its credited
controls:

| Average credited score | Control tier | Band reduction |
| ---------------------- | ------------ | -------------- |
| ≥ 3.5 | Strong | −2 |
| 2.0–3.49 | Moderate | −1 |
| < 2.0 | Weak | 0 |
| no credited control (none linked, untested, or unevidenced) | None / Unproven | 0 |

**Residual band index = max(Low, inherent band index − reduction)** with the ordering
`Low(0) < Moderate(1) < High(2) < Critical(3)`. Residual never falls below Low. This is the
conservative, fail-closed rule: the skill **cannot** manufacture residual reduction from an
untested or unevidenced control.

## Risk appetite

Each category has an appetite band (or a `default`). A residual is **over appetite** when its
band index exceeds the category appetite index. Every over-appetite residual **requires** a
recorded treatment action; a residual above appetite with no treatment action is a
completeness failure surfaced in Treatment Actions and Limitations, never hidden.

## Hard boundaries (fail closed)

- No **acceptance** of a residual rating; no **approval/finalization** of the assessment.
- No **risk closure**, **attestation sign-off**, or management **sign-off** recorded.
- No **filing** or **write to the risk register / GRC system of record**.
- No **control credit** for untested or unevidenced controls.
- No **unsupported assertion** — every rating, effectiveness claim, and KRI value is cited.
- No **binding risk decision** presented as final; residual ratings are recommendations for
  human adjudication.

## Required draft contents

Scope and basis; the risk inventory with owners; inherent scoring with rationale; the control
environment with proven/credited status and evidence; residual ratings tied to the
deterministic mapping with appetite comparison; linked KRIs; treatment actions for every
over-appetite residual; an evidence register; disclosed limitations/assumptions; and the
recorded (pending) approvals. Standing note: "Draft enterprise risk assessment for human
review only; no risk has been accepted, no residual rating approved, no assessment finalized,
and nothing filed or written to the risk system of record."
