# Domain Rules — risk-control-self-assessment-assistant

Orientation references: Basel operational-risk / sound-management principles, COSO ERM and
Internal Control–Integrated Framework, and the three-lines model (first line owns and
assesses risk; second line independently challenges; third line assures). The firm's ERM
policy, RCSA standard, risk taxonomy, **risk appetite**, and control library take precedence
and are **versioned contracts**. Scoring below is documented configuration, not judgment.

## Inherent risk scoring (deterministic)

Inherent score = **impact (1–5) × likelihood (1–5)** → level → band:

| Inherent score | Level | Band |
| -------------- | ----- | ---- |
| 1–4 | 1 | Low |
| 5–9 | 2 | Medium |
| 10–14 | 3 | High |
| 15–25 | 4 | Critical |

Impact and likelihood anchors come from the firm's RCSA rating scale; they are inputs to the
skill, not invented here. A statement with no impact/likelihood is rejected at input.

## Control effectiveness (deterministic, evidence-gated)

Each control carries a **design** rating and an **operating** rating, each one of
`Effective` / `Partially Effective` / `Ineffective`. Overall effectiveness:

| Condition | Overall effectiveness |
| --------- | --------------------- |
| Design = Effective **and** Operating = Effective | **Effective** |
| Design = Ineffective **or** Operating = Ineffective | **Ineffective** |
| Otherwise | **Partially Effective** |
| A crediting conclusion (Effective / Partially Effective) with **no evidence** | **Unsubstantiated** (downgraded; not credited) |

**Evidence gate (no unsupported assertions):** a control may only be *credited* with
mitigation when it carries evidence (control test, KRI, loss event, or attestation with a
reference and date). A rated-but-unevidenced control is reported as **Unsubstantiated**, is
**not** credited toward residual reduction, and its gap is raised as a challenge. This is the
core R3 control against overstating the control environment.

## Residual risk (deterministic)

Residual reduces the inherent **level** by the strongest (best) mitigating control:

| Overall control effectiveness (best control) | Level reduction |
| -------------------------------------------- | --------------- |
| Effective | −2 |
| Partially Effective | −1 |
| Ineffective / Unsubstantiated / no control | 0 |

`residual_level = max(1, inherent_level − reduction)`; residual band from the level table.
Residual is a *self-assessed* rating for human review, never a binding risk decision.

## Remediation trigger (deterministic)

Remediation is **required** when `residual_level > appetite_level` (appetite from the
Low/Medium/High/Critical scale) **or** **any** mapped control is `Ineffective` (evaluated
independently of best-control selection, so an Ineffective control is never masked by an
earlier zero-reduction control such as an Unsubstantiated one). Owner and due date
are supplied by a human; where absent the draft flags `TBD`. Status vs. `as_of_date`:
`open` (due in future), `overdue` (past due), `unplanned` (no due date). The assistant does
not close, waive, or accept a remediation item.

## Statement / control challenges (decision-support prompts, not decisions)

The assistant surfaces challenges for the human reviewer, including:
- a **material inherent risk with no controls mapped** (uncontrolled exposure);
- a control **rated but unevidenced** (evidence gap → Unsubstantiated);
- a **loss event or KRI breach** recorded while a key control reads Effective/Partially
  Effective (corroborate before sign-off);
- residual **above appetite** without a remediation action.

## Hard boundaries (fail closed)

- **Draft-only.** Never sign off, attest, self-certify, close, finalize, or write the GRC
  system of record; never make or record a **risk-acceptance** decision.
- **No autonomous residual/appetite decision.** The residual rating and remediation triggers
  are computed for human adjudication; first-line management and second-line challenge decide.
- **No unsupported assertions.** No credited control conclusion without evidence.
- **No independent-challenge substitution.** The assistant is first-line drafting support; it
  cannot stand in for the second-line independent challenge/validation.

## Required package contents (see assets/output-template.md)

Assessment scope; risk & control assessment (inherent, controls, residual); residual
summary; evidence map; challenges & gaps; remediation plan; and a required-approvals block
(control owner, first-line sign-off, second-line challenge) recorded as `pending`.
