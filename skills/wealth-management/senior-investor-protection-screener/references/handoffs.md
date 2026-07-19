# Adjacent-Skill Handoffs — senior-investor-protection-screener

This skill produces a cited **senior-investor concern pack** (`screening_id`) with a suggested
review disposition and stops. It does not adjudicate, decide, hold, file, contact, or close.
Adjudication and any regulated action are performed by a trained human (advisor + branch
supervisor / compliance / senior-protection team) and, where relevant, the downstream skills
below.

## Downstream (route the human/reviewer to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `suspicious-activity-report-drafter` | The reviewer decides a SAR may be warranted (draft-only, compliance-approved, human-filed) | `screening_id` + evidence |
| `suitability-reg-bi-reviewer` | The concern is really about whether a recommendation/product is suitable, not exploitation | client profile + recommendation |
| `vulnerable-customer-support-assistant` | The client needs support accommodations or a specialist referral rather than a fraud/exploitation review | client-provided context |
| `complaint-resolution-assistant` | The matter is a complaint about handling/service, not an exploitation concern | complaint intake |
| `client-review-preparer` | The request is routine client-review preparation with no concern signals | goals + holdings + meeting context |

## Human / operations handoffs (no catalog skill — route in prose)

- **Branch supervisor / compliance / senior-protection committee** — owns the adjudication:
  whether exploitation or capacity concerns are substantiated, whether a FINRA Rule 2165
  temporary hold is placed, and whether to engage the trusted contact.
- **BSA/AML officer** — owns any SAR filing decision and the regulatory-report pathway.
- **Adult Protective Services / state securities or APS regulator** — external reporting is a
  human, authorized-firm action; the skill never contacts or files with these bodies.
- **Licensed advisor / legal** — any personalized investment, legal, or tax question, and any
  suitability approval.

## Upstream (may call this skill)

`omnichannel-case-orchestrator` and advisor/service-desk skills may request a concern pack.
An account-level anomaly pack from `account-anomaly-screener` (banking) may accompany the
request as supporting evidence. A scheduled monitor is **not** used here (this skill is
interactive, `aws-fsi-scheduled-agent: no`).

## Duplicate-execution prevention

- This skill computes and evidences **concern signals only**; it must not reach a disposition
  determination, contact the client/trusted contact, place a hold, file, or close — those
  belong to the human adjudicator and the downstream skills.
- Downstream skills reuse the `screening_id` evidence rather than recomputing signals.
