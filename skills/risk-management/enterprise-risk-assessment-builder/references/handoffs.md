# Adjacent-Skill Handoffs — enterprise-risk-assessment-builder

This skill is the **assembler**: it links risks, scenarios, controls, residual ratings,
indicators, owners, evidence, and treatment actions into a controlled **draft** enterprise
risk assessment. Component analyses are produced by specialist skills upstream; adjudication
and any system-of-record change happen with humans downstream. This skill never re-performs a
specialist's analysis and never makes the acceptance/approval decision.

## Upstream (feeds component evidence into this skill)

| Upstream skill | Provides |
| -------------- | -------- |
| `risk-control-self-assessment-assistant` | Control design/operating effectiveness scores and RCSA evidence |
| `key-risk-indicator-monitor` | KRI values, thresholds, breach and trend status |
| `operational-risk-event-analyzer` | Loss and near-miss events, root-cause themes, impacts |
| `stress-test-scenario-designer` | Severe-but-plausible scenarios and transmission channels |
| `third-party-risk-assessor` | Vendor criticality, resilience, and exit-plan evidence |
| `concentration-risk-monitor` | Counterparty / sector / provider concentration signals |

This skill consumes these outputs as **cited inputs**; it does not recompute control tests,
KRIs, loss classifications, scenarios, vendor assessments, or concentrations. If a component
input is missing or stale, the affected risk is set `needs-evidence` and disclosed in
Limitations & Assumptions.

## Downstream (this skill hands the draft to)

| Downstream skill / actor | When | Handoff artifact |
| ------------------------ | ---- | ---------------- |
| **Human adjudication** — Risk & Control Owner, then Enterprise Risk Management (2nd line), then Risk Committee / CRO | Always, before any acceptance, approval, closure, attestation, or register write | Draft assessment + evidence register + pending approvals |
| `regulatory-exam-response-packager` | The approved assessment is requested in a regulatory exam or inquiry | Human-approved assessment + provenance |
| `audit-evidence-packager` | Internal/external audit requests the assessment as evidence | Human-approved assessment + chain of custody |
| `regulatory-change-impact-analyzer` | A new obligation must be mapped back into risks/controls | Risk/control linkage for impact mapping |

Acceptance of residual ratings, approval/finalization of the assessment, risk closure,
attestation sign-off, and any write to the risk register are **human/committee actions via the
approval broker** — not adjacent skills and never this skill.

## Duplicate-execution prevention

- This skill **does not** perform RCSA scoring, KRI monitoring, loss-event analysis, scenario
  design, third-party assessment, or concentration monitoring — those belong upstream.
- It **does not** adjudicate, approve, close, attest, file, or write the risk register — those
  are human decisions downstream.
- The assessment carries a durable `assessment_id` plus `template_version`/`config_version`
  so the same draft is reviewed and versioned, not silently re-generated.
