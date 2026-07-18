# Adjacent-Skill Handoffs — claims-file-reviewer

This skill produces a cited **claim-file review pack** (`review_id`) — chronology, findings,
and evidence — and stops. It does not adjudicate coverage, set reserves, pay, close, or file.

## Upstream (may call this skill)

| Upstream skill | When | Handoff artifact |
| -------------- | ---- | ---------------- |
| `claims-triage-assistant` | A triaged claim needs a full documentation/traceability review before adjudication | claim_id + triage classification |

Triage classifies and routes; this skill reviews the assembled file. A scheduled monitor is
**not** used here (`aws-fsi-scheduled-agent: no`).

## Downstream (route the human/reviewer to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `claims-fraud-referral-assistant` | Fraud indicators surfaced; a referral must be drafted (draft-only, no fraud finding) | `review_id` + flagged evidence |
| `reserving-analysis-assistant` | Reserve adequacy / development / uncertainty needs actuarial analysis | `review_id` + reserve findings |
| `subrogation-opportunity-screener` | Recovery / subrogation potential against a responsible party | claim_id + loss facts |
| `coverage-gap-analyzer` | The question is a needs-vs-terms coverage-gap analysis, not a file review | policy + exposures |
| `policy-wording-comparator` | A form/endorsement wording question needs clause-level comparison to filed forms | policy forms + versions |
| `policy-document-explainer` | The user wants a plain-language explanation of a policy clause | policy document |

## Human / specialist handoffs (no catalog skill)

The **coverage and reserve decisions themselves** always go to a licensed adjuster, claims
manager, or coverage counsel — there is no skill that makes them. A confirmed fraud
disposition belongs to the Special Investigations Unit; litigation strategy belongs to
claims legal. This skill routes to those humans in prose, never to an invented skill.

## Duplicate-execution prevention

- This skill evidences **findings only**; it must not adjudicate, contact the claimant, pay,
  reserve, close, or file — those belong to the human and the downstream draft-only skills.
- Downstream skills reuse the `review_id` evidence rather than re-reviewing the file.
