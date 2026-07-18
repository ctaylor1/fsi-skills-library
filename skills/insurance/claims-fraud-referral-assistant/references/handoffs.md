# Adjacent-Skill Handoffs — claims-fraud-referral-assistant

Drafting a fraud referral is a **separate control activity** from claim triage, claim-file
review, and — critically — from SIU investigation and claim adjudication. Each has distinct
entitlements, evidence depth, and outcomes, and they route to one another explicitly.

## Downstream (this skill hands off to)

| Destination | When | Handoff artifact |
| ----------- | ---- | ---------------- |
| **Special Investigations Unit (SIU)** — a human investigative function; **no catalog skill** performs SIU adjudication | Any `refer-to-siu` recommendation | `referral_id` + drafted referral package (indicators, evidence, citations) with approvals pending |
| `subrogation-opportunity-screener` | The pattern is a third-party recovery opportunity, not suspected fraud | claim_id + responsible-party evidence |
| `claims-file-reviewer` | A coverage/reserve or documentation question surfaces alongside the indicators | claim_id + open-issue evidence |

The SIU handoff is deliberately to a **human specialist**: no skill in the catalog makes a
fraud finding or accepts a referral, and this skill must not simulate one. It emits a durable
`referral_id` and a draft package; the licensed SIU investigator decides.

## Upstream (feeds this skill)

| Upstream skill | Provides |
| -------------- | -------- |
| `claims-triage-assistant` | Triaged claims where a fraud-review need was flagged for human confirmation |
| `claims-file-reviewer` | A reviewed claim file whose open issues include possible fraud indicators |

This skill is **interactive** (`aws-fsi-scheduled-agent: no`); an upstream monitor may
*populate* a candidate queue but must not draft referrals or act.

## Duplicate-execution prevention

- This skill **does not** investigate, adjudicate fraud, or decide coverage/claims — those
  belong to human SIU / adjudication downstream.
- SIU consumes the `referral_id` + package rather than re-scoring from scratch.
- A `monitor` or `insufficient-indicators` outcome is **not** a clearance — it is a routing
  recommendation a human may revisit; no case is closed here.
