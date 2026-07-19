# Adjacent-Skill Handoffs — operational-resilience-scenario-tester

This skill produces a cited **scenario-test pack** (`test_id`) — severity/plausibility flags,
impact-tolerance test outcomes, dependency coverage, decision and recovery evidence, lessons,
and a suggested review disposition — then stops. It does not report to a regulator, update a
register, coordinate a live incident, act on customers, or close a case.

## Downstream (route the human / reviewer to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `operational-resilience-reporter` | Regulatory resilience reporting, jurisdictional templates, or critical-service / critical-third-party register updates are needed | `test_id` + tolerance-test outcomes + evidence |
| `cyber-incident-response-coordinator` | A *real* incident (not a test) needs chronology, roles, containment, and communications coordination | scenario/threat context |
| `service-recovery-assistant` | Actual customers were impacted and need remediation and communications drafted | affected-service + impact summary |
| `ransomware-readiness-assessor` | A deeper ransomware-specific readiness assessment (identity, segmentation, backups, recovery) is wanted | `test_id` + relevant scenario |
| `third-party-cyber-risk-reviewer` | A critical third-party dependency surfaced by a scenario needs a supplier security/resilience deep dive | dependency + supplier reference |

## Not this skill (distinct scope)

- **Financial / capital stress testing** (transmission channels, reverse-stress thresholds)
  is `stress-test-scenario-designer` in Risk Management — different discipline and register.
- **Regulatory exam / inquiry response packaging** is `regulatory-exam-response-packager`.

## Upstream (may call this skill)

An operational-resilience programme lead or a self-assessment cycle may request a scenario
test. This skill is interactive (`aws-fsi-scheduled-agent: no`); it is not run as a scheduled
monitor.

## Duplicate-execution prevention

- This skill computes and evidences **test outcomes and a suggested disposition only**; it
  must not reach a resilience determination, sign off, file, update a register, or close a
  case — those belong to the human adjudicator and the downstream skills above.
- Downstream skills reuse the `test_id` evidence rather than re-running the scenario test.
