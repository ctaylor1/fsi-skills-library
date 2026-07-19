# Adjacent-Skill Handoffs — identity-access-reviewer

This skill produces a cited **access-review pack** (`review_id`) with findings, evidence, and
**staged revocation candidates**, then stops. It does not decide access, execute revocations,
certify entitlements, or close the review — those are human control-owner and IAM-operations
actions.

## Downstream (route the human/reviewer to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `security-alert-triage-assistant` | A finding suggests active misuse of an identity (e.g. dormant privileged account suddenly used) that needs enrichment/prioritization as a security alert | `review_id` + implicated accounts |
| `phishing-and-bec-investigator` | Suspected account takeover / BEC behind an anomalous grant or login | `review_id` + account + login evidence |
| `cloud-security-posture-reviewer` | The access issue is a cloud IAM misconfiguration (over-broad policy, public role) rather than a grant-level review item | affected cloud identities/roles |
| `third-party-cyber-risk-reviewer` | The identities/entitlements belong to a supplier or its subcontractors | `review_id` + vendor scope |
| `cyber-incident-response-coordinator` | The review surfaces a live incident (confirmed compromise) needing coordinated response | `review_id` + evidence bundle |
| `operational-resilience-reporter` | Aggregate access-control posture must be reported to a governance/regulatory audience | `review_id` + finding summary |

## Non-skill (human / operations) handoffs

- **Executing an approved revocation** — after a control owner approves a staged candidate,
  the actual change runs through the organization's IAM provisioning / joiner-mover-leaver
  process (privileged-access management, ticketed deprovisioning). That is an authorized
  human/system action **outside this skill**; there is no catalog skill that executes writes.
- **Certification sign-off** — recording a certification decision is the control owner's
  action in the IGA campaign tool; this skill only supplies the evidence that a grant is
  overdue or unjustified.

## Upstream (may call this skill)

A periodic access-certification campaign, an audit request, or a control owner preparing for
recertification may request a review pack. This skill is interactive
(`aws-fsi-scheduled-agent: no`) — it is not a scheduled monitor.

## Duplicate-execution prevention

- This skill computes **findings, evidence, and staged candidates only**; it must not reach
  an access decision, execute a change, or certify — those belong to the human control owner,
  IAM operations, and the downstream skills.
- Downstream skills reuse the `review_id` evidence rather than recomputing findings.
