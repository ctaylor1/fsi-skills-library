# Adjacent-Skill Handoffs — operational-resilience-reporter

This skill is a **reporting/packaging** activity. It consumes evidence produced by upstream
resilience and risk skills and produces a **draft** report package. It never performs the
underlying investigation, testing, assessment, or the regulatory filing.

## Upstream (feeds this skill)

| Upstream skill | Provides | Handoff artifact |
| -------------- | -------- | ---------------- |
| `operational-resilience-scenario-tester` | Severe-but-plausible scenario / impact-tolerance test results | Test records with outcomes and within/outside-tolerance flags |
| `cyber-incident-response-coordinator` | Incident timelines, severity, root-cause/remediation refs | Incident records for the reporting period |
| `operational-risk-event-analyzer` | Operational-risk event detail behind incidents | Event evidence and references |
| `third-party-cyber-risk-reviewer` | Critical-third-party cyber assessments | Third-party criticality + risk evidence |
| `third-party-risk-assessor` | TPRM assessments feeding the critical-third-party register | Third-party register entries + contract/exit refs |

## Downstream / adjacent (this skill hands to)

| Downstream skill / role | When | Handoff artifact |
| ----------------------- | ---- | ---------------- |
| `board-committee-pack-builder` | Draft resilience report feeds a board/committee pack | Draft report package + citations |
| `regulatory-exam-response-packager` | The report is requested as part of an exam/information request | Draft report package + evidence index |
| `audit-evidence-packager` | Internal audit needs the resilience evidence set | Draft report package + register/test citations |
| `regulatory-change-impact-analyzer` | The jurisdiction rule/template version changed and the pack needs re-interpretation | `ruleset_version` gap + affected sections |

## Human / specialist handoffs (no catalog skill — do in prose, never invent a skill)

- **Regulatory notification/submission** — a licensed **regulatory-reporting owner** decides
  whether and when to notify a supervisor and performs the filing. This skill only records
  the human-provided notification *status*; it never notifies or submits.
- **Board/executive attestation** — the accountable executive and the board attest through
  governance, not through this skill; the package records attestation *status* only.
- **Legal / compliance sign-off** — where the report has legal consequence, legal and
  compliance adjudicate before any external delivery.

## Duplicate-execution prevention

- This skill does **not** run scenario tests, investigate incidents, or perform TPRM
  assessments — those belong to the upstream skills, and their outputs are consumed as
  evidence here.
- It does **not** file, submit, or attest — those are human acts downstream of the draft.
- Sections lacking upstream evidence are emitted as `gap` for human input, never fabricated.
