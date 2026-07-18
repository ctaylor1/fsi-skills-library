# Adjacent-Skill Handoffs — claim-readiness-checker

This skill produces a cited **claim readiness assessment** (`readiness_id`) and stops. It
does not adjudicate, decide coverage, price, close, or refer — it reports what is present,
missing, expiring, or inconsistent so the claim reaches an adjuster complete.

## Downstream (route the human/reviewer to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `claims-triage-assistant` | The claim is complete/submitted and needs severity, complexity, urgency, and coverage-question classification for assignment | `readiness_id` + claim record |
| `claims-file-reviewer` | Adjuster-side review of the open file for coverage evidence, chronology, and missing documentation (this skill is pre-submission, that skill is carrier-side) | `readiness_id` + document manifest |
| `claim-denial-appeal-helper` | The claim was denied and the policyholder wants to understand why and assemble an appeal | claim + denial notice |
| `coverage-gap-analyzer` | The user actually wants to know whether their coverage/limits fit their exposure, not whether the claim file is complete | policy + stated needs |
| `policy-document-explainer` | The user wants the policy terms/deadlines explained rather than a readiness check | policy document |
| `claims-fraud-referral-assistant` | A reviewer (not this skill) decides potential-fraud indicators warrant a referral | claim + evidence, human-initiated |

## Upstream (may call this skill)

`submission-intake-triager` and claims intake/service-desk skills may request a readiness
check on a newly received claim package. A scheduled monitor is **not** used here (this skill
is interactive, `aws-fsi-scheduled-agent: no`).

## Duplicate-execution prevention

- This skill checks **completeness and timeliness only**; it must not reach a coverage,
  eligibility, settlement, or fraud conclusion, contact the claimant, or write the claim
  system of record — those belong to the human adjuster and the downstream skills.
- Downstream skills reuse the `readiness_id` assessment and its citations rather than
  re-inventorying the file.
