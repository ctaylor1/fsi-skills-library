# Adjacent-Skill Handoffs — cloud-security-posture-reviewer

This skill produces a cited **cloud posture review pack** (`review_id`) — findings, evidence,
and recommended remediation — and stops. It does not remediate, close/waive findings, grant
exceptions, attest compliance, or write a system of record.

## Upstream (may call this skill)

| Upstream skill | When | Handoff artifact |
| -------------- | ---- | ---------------- |
| `security-alert-triage-assistant` | A misconfiguration alert needs full posture context and cited evidence before analyst work | alert + affected `resource_id`s |
| `cyber-incident-response-coordinator` | An incident needs a point-in-time posture snapshot of the affected scope as evidence | account scope + `as_of` |

A scheduled monitor is **not** used here (`aws-fsi-scheduled-agent: no`); this skill is
interactive decision support.

## Downstream (route the human/reviewer to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `identity-access-reviewer` | Identity findings need deep entitlement / privileged-access / certification review and staged revocations | `review_id` + identity findings |
| `vulnerability-prioritization-assistant` | A finding intersects a known exploitable vulnerability on the same resource | `review_id` + resource list |
| `data-loss-prevention-incident-assistant` | A public exposure may already have led to data loss and needs incident investigation | `review_id` + exposed-resource evidence |
| `cyber-incident-response-coordinator` | Indicators point to active compromise rather than a latent misconfiguration | affected scope + evidence |
| `third-party-cyber-risk-reviewer` | The posture belongs to a supplier/third party rather than an owned account | supplier + posture evidence |
| `operational-resilience-reporter` | Findings feed a regulatory resilience/incident/dependency report | `review_id` + findings |

## Human / specialist handoffs (no catalog skill)

The **remediation deployment**, **risk acceptance**, **exception/waiver approval**, and
**compliance attestation** themselves always go to the cloud/platform owner, the security
control owner, or CISO/GRC — there is no skill that makes them. This skill routes to those
humans in prose, never to an invented skill.

## Duplicate-execution prevention

- This skill evidences **findings and recommendations only**; it must not remediate, close,
  waive, attest, or write a system of record — those belong to the human and the downstream
  skills.
- Downstream skills reuse the `review_id` evidence rather than re-scanning the posture.
