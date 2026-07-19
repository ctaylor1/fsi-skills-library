# Adjacent-Skill Handoffs — customer-risk-rating-reviewer

This skill produces a cited **rating-review pack** (`review_id`) and stops. It does not
decide the rating, approve an override, dispose of a trigger, close a review, or file.

## Upstream (may call this skill)

| Upstream skill | When | Handoff artifact |
| -------------- | ---- | ---------------- |
| `kyc-customer-due-diligence-screener` | An onboarding/periodic CDD screen needs the rating recalculated/challenged (the CDD screener never sets a rating) | customer + factors + rating of record |
| `aml-alert-triager` | First-line triage flags that a monitoring alert may warrant a re-rating | customer + trigger event |
| `regulatory-exam-response-packager` | An exam request asks for the rating rationale and QA evidence for a customer | customer + `review_id` |

## Downstream (route the human/reviewer to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `enhanced-due-diligence-packager` | Recomputation reaches High/Prohibited or a PEP floor — assemble source-of-wealth/funds and ownership evidence | `review_id` + recomputed band |
| `sanctions-match-adjudicator` | A potential sanctions nexus/PEP match sits behind a factor and needs a specialist disposition | customer + factor evidence |
| `adverse-media-investigator` | An adverse-media trigger needs entity-resolved assessment | trigger + `review_id` |
| `transaction-monitoring-alert-investigator` | A monitoring-alert trigger needs substantive investigation | trigger + `review_id` |
| `beneficial-ownership-verifier` | The geography/ownership factor rests on unverified ownership data | customer + ownership rows |
| `suspicious-activity-report-drafter` | The adjudicator decides a SAR may be warranted (draft-only, human-filed) | `review_id` + evidence |

If no catalog skill fits a needed step, route it to the human owner in prose — the qualified
compliance officer / MLRO adjudicates the rating and any override, and the KYC/AML case owner
remediates data gaps. Never invent a skill name.

## Duplicate-execution prevention

- This skill **recomputes and evidences** a rating challenge only; it must not reach a rating
  decision, approve an override, dispose of a trigger, or close a review — those belong to the
  human adjudicator and the downstream skills.
- Downstream skills reuse the `review_id` recomputation and evidence rather than re-scoring the
  factors, and each carries its own disposition/closure controls.
