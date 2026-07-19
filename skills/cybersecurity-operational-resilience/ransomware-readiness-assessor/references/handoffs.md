# Adjacent-Skill Handoffs — ransomware-readiness-assessor

This skill produces a cited **ransomware-readiness assessment** (`readiness_id`) with gap
findings, evidence, and **staged remediation candidates**, then stops. It does not decide
readiness, accept risk, execute remediation, attest, file a report, or close the assessment —
those are human control-owner and downstream-team actions.

## Downstream (route the human/control owner to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `identity-access-reviewer` | An identity gap needs grant-level detail (privileged entitlements, SoD, dormant/orphaned accounts) beyond the MFA/tiering posture | `readiness_id` + implicated identity scope |
| `cloud-security-posture-reviewer` | A segmentation/detection gap is a cloud misconfiguration (over-broad policy, missing logging/encryption) rather than a service-level control gap | affected cloud services/roles |
| `vulnerability-prioritization-assistant` | A detection/exposure gap should be worked as prioritized vulnerability remediation on the critical assets | `readiness_id` + affected assets |
| `third-party-cyber-risk-reviewer` | A critical-third-party resilience gap needs full supplier security/resilience assurance | `readiness_id` + vendor scope |
| `operational-resilience-scenario-tester` | The exercise gap should be closed by designing/documenting a severe-but-plausible disruption test or ransomware tabletop | `readiness_id` + scenario scope |
| `operational-resilience-reporter` | The readiness posture must be recorded in critical-service/third-party registers or reported to a governance/regulatory audience | `readiness_id` + finding summary |
| `data-loss-prevention-incident-assistant` | A concern involves potential data exfiltration / double-extortion exposure rather than readiness controls | affected data/systems |
| `security-alert-triage-assistant` | A suspected ransomware precursor or active alert needs enrichment and prioritization | implicated assets/identities |
| `cyber-incident-response-coordinator` | A **live or suspected ransomware incident** is underway — this is not a readiness assessment; hand off immediately | scope + initial evidence |

## Non-skill (human / operations) handoffs

- **Executing a remediation** — after a control owner approves a staged candidate, the actual
  change (enforcing MFA, re-segmenting, provisioning immutable backups, running a restore test)
  runs through the organization's change-management / engineering process. That is an authorized
  human/system action **outside this skill**; there is no catalog skill that executes writes.
- **Readiness attestation / risk acceptance** — signing a readiness attestation or accepting a
  gap's residual risk is the accountable owner's governance decision, recorded in the GRC tool;
  this skill only supplies the evidence and staged recommendations.
- **Regulatory filing** — where a resilience/incident report must be filed, that is done by the
  accountable function; drafting such reports is `operational-resilience-reporter`'s scope.

## Upstream (may call this skill)

A periodic resilience review, an audit request, a board/regulatory readiness question, or a
control owner preparing for recertification may request an assessment. This skill is interactive
(`aws-fsi-scheduled-agent: no`) — it is not a scheduled monitor.

## Duplicate-execution prevention

- This skill computes **findings, evidence, and staged candidates only**; it must not reach a
  readiness decision, accept risk, execute a change, attest, file, or close — those belong to the
  human control owner and the downstream skills/teams.
- Downstream skills reuse the `readiness_id` evidence rather than recomputing the assessment.
