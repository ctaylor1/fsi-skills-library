# Adjacent-Skill Handoffs — kyc-customer-due-diligence-screener

This skill produces a cited **CDD screening pack** (`screening_id`) with a recommended
review track and stops. It does not adjudicate matches, decide the relationship, rate,
close, or file — those belong to specialist skills and a human analyst.

## Upstream (may run before this skill)

| Upstream skill | When | Handoff artifact |
| -------------- | ---- | ---------------- |
| `customer-onboarding-document-checker` | Confirms the onboarding package's required documents are present and consistent before CDD screening | Completed document package |

## Downstream (route the analyst / specialist to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `sanctions-match-adjudicator` | `sanctions_potential_match` fired — a potential sanctions/watchlist match needs a documented disposition recommendation for authorized review | `screening_id` + the potential match |
| `enhanced-due-diligence-packager` | Track is `EDD-Recommended` and the analyst confirms EDD — assemble source-of-wealth/funds, ownership, geography, adverse-media, and control evidence | `screening_id` + fired risk signals |
| `beneficial-ownership-verifier` | `ubo_below_coverage` / `ubo_unverified` — map and verify the full legal/control ownership chain | `screening_id` + owner rows |
| `adverse-media-investigator` | `adverse_media_flag` — assess credibility, distinguish allegation from finding, resolve the entity | `screening_id` + media indicators |
| `customer-risk-rating-reviewer` | The analyst decides a risk-rating (re)assessment is warranted — recalculate/challenge under approved methodology | `screening_id` + evidence |
| `transaction-monitoring-alert-investigator` | Screening surfaces a monitoring concern needing investigation (not adjudicated here) | `screening_id` + context |
| `suspicious-activity-report-drafter` | The analyst decides a SAR may be warranted (draft-only, human-filed) | `screening_id` + evidence |

## Human / operations handoffs (no catalog skill)

- **CDD/KYC decision, onboarding, exit, and case closure** are made by the KYC / onboarding
  analyst and the responsible approver — never by this skill.
- **Sanctions/PEP disposition and any regulatory filing** are performed by the authorized
  specialist and compliance officer after human adjudication.

## Duplicate-execution prevention

- This skill computes and evidences **signals and a recommended track only**; it must not
  adjudicate a match, decide the relationship, set a rating, close, or file — those belong to
  the downstream skills and the human analyst.
- Downstream skills reuse the `screening_id` evidence rather than recomputing signals.
