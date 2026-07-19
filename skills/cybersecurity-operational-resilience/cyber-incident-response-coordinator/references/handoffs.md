# Adjacent-Skill Handoffs — cyber-incident-response-coordinator

This skill maintains the **coordination record** (`coordination_id`) — chronology, roles,
evidence, decisions, tasks, communications, dependencies, and post-incident actions — and stops
there. It does not investigate to disposition, decide, act, close, or file. It routes work to
the right investigation, remediation, reporting, and human owners.

## Upstream (may feed this skill)

| Upstream skill | Hands over |
| -------------- | ---------- |
| `security-alert-triage-assistant` | A triaged, enriched alert that has escalated to a declared incident |
| `phishing-and-bec-investigator` | A BEC/phishing case that has become a coordinated incident |
| `data-loss-prevention-incident-assistant` | A DLP exfiltration/policy case escalated to incident coordination |

## Downstream / lateral (route the human / reviewer to)

| Skill | When | Handoff artifact |
| ----- | ---- | ---------------- |
| `identity-access-reviewer` | Compromised identities/entitlements need review and staged revocation | Affected identities + `coordination_id` |
| `vulnerability-prioritization-assistant` | An exploited vulnerability needs prioritization/remediation planning | Exploited CVE/asset + evidence |
| `cloud-security-posture-reviewer` | A cloud misconfiguration was exploited or exposed data | Affected resources + evidence |
| `operational-resilience-reporter` | Regulatory/breach reporting is being considered (drafting, jurisdiction templates) | `coordination_id` + evidence + impact/impact-tolerance data |
| `third-party-cyber-risk-reviewer` | A supplier/third party is implicated in the incident | Supplier + incident linkage |
| `ransomware-readiness-assessor` | Post-incident readiness/recovery gaps should be assessed | Lessons learned + affected controls |
| `operational-resilience-scenario-tester` | Lessons learned should feed a severe-but-plausible scenario test | Post-incident actions + dependency map |
| `payment-fraud-case-investigator` | The incident involves payment fraud needing case investigation | Focal transactions + `coordination_id` |
| `suspicious-activity-report-drafter` | A reviewer decides a SAR may be warranted (draft-only, human-filed) | Evidence + `coordination_id` |

## Human / specialist handoffs (no catalog skill — route in prose)

- **Legal / privacy counsel** — owns the breach-notification decision, privilege, and any
  regulator/customer commitment. The coordinator only reminds that clocks may apply.
- **Executive crisis-management leadership / incident commander** — owns severity confirmation,
  major-incident declaration, closure, and public statements.
- **External DFIR / forensics retainer** — owns imaging, deep forensic analysis, and attribution.
- **Law-enforcement liaison** and **cyber-insurance carrier** — owned by legal/executive, not
  triggered by this skill.
- **HR** (insider-implicated cases) and **communications/PR** — owned by their functions.

## Duplicate-execution prevention

- This skill **coordinates and records only**; it must not reach a disposition, decide severity,
  execute a containment/remediation action, close the incident, or file — those belong to the
  humans and the downstream skills above.
- Downstream skills reuse the `coordination_id` evidence rather than recomputing the record.
- A scheduled monitor is **not** used here (`aws-fsi-scheduled-agent: no`); the skill is an
  interactive copilot invoked during an active incident.
