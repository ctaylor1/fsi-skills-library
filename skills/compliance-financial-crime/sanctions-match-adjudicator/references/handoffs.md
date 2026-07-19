# Adjacent-Skill Handoffs — sanctions-match-adjudicator

Screening, adjudication (this skill), and the blocking/reporting decision are **separate
control activities** with different entitlements. This skill consumes a documented screening
hit, emits a durable `case_id` + evidence bundle, and hands a **recommendation** to an
authorized human.

## Upstream (feeds this skill)

| Upstream | When | Handoff artifact |
| -------- | ---- | ---------------- |
| Screening engine / payment filter (platform service, no catalog skill) | A real-time or batch filter raises a potential match | `alert_id` + `screening_provenance` + subject/matched records |
| `kyc-customer-due-diligence-screener` | Onboarding/periodic screening surfaces a potential list match | subject record + matched list entry |
| `aml-alert-triager` | Triage surfaces a sanctions/adverse-media proximity flag on an alert | `case_id` + flag evidence |

A hit with **no** documented screening provenance is refused here and routed back to the
screening engine / `kyc-customer-due-diligence-screener`; adjudication never self-generates a
match.

## Downstream / lateral (this skill routes to — recommendations, not actions)

| Skill | When | Handoff artifact |
| ----- | ---- | ---------------- |
| `beneficial-ownership-verifier` | An ownership / 50%-Rule nexus needs UBO verification | `case_id` + ownership evidence |
| `enhanced-due-diligence-packager` | A true/potential match needs deeper EDD on the subject | `case_id` + evidence bundle |
| `adverse-media-investigator` | Corroborating adverse media on the subject is needed | subject + evidence bundle |
| `customer-risk-rating-reviewer` | A match should feed a customer risk-rating review | subject_id + disposition evidence |
| `transaction-monitoring-alert-investigator` | The hit reveals a broader AML pattern to investigate | `case_id` + transaction context |
| `suspicious-activity-report-drafter` | **Only after** an officer adjudicates a true match and decides a SAR may be warranted (never autonomous) | the officer-approved case |

## Human / operations handoffs (no catalog skill — prose)

- **Authorized sanctions officer / OFAC compliance / MLRO** — makes the true/false-match
  determination and the block, reject, release, unblock, closure, and blocking/OFAC-report
  decisions. This is the mandatory human adjudication for every disposition.
- **L2 / senior sanctions review** — receives `recommend-potential-match-l2-review` and
  conflict-guard cases for a second, senior look.

## Duplicate-execution prevention

- This skill **does not** screen, verify ownership, investigate AML typologies, or draft a SAR —
  those belong to the skills above.
- The sanctions officer consumes the `case_id`/bundle rather than re-adjudicating.
- A `possible-duplicate` link is resolved by a human, not auto-merged here.
