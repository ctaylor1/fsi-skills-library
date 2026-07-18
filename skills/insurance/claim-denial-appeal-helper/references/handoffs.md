# Adjacent-Skill Handoffs — claim-denial-appeal-helper

This skill produces a cited **appeal package** (`appeal_id`): an explanation of the denial, an
evidence map with gaps, an administrative deadline, and an argument scaffold. It stops at a
draft that a human reviews and delivers. It does not decide coverage, give legal advice, or
file.

## Downstream (route the human/member to)

| Downstream skill / actor | When | Handoff artifact |
| ------------------------ | ---- | ---------------- |
| **Licensed attorney (external, not a skill)** | The member asks about legal rights, damages, bad faith, or litigation | Nothing exported by this skill — refer out |
| `policy-document-explainer` | The member wants plain-language explanation of the plan wording rather than an appeal | plan_id + provision |
| `coverage-gap-analyzer` | The member wants to understand coverage gaps across the policy, not appeal one denial | policy + claim context |
| `policy-wording-comparator` | The dispute turns on comparing the plan text to another version/plan | plan documents |
| Independent external review (IRO) / plan appeals unit | After a human decides to submit; the plan's own process files and adjudicates | `appeal_id` package (human-delivered) |

## Upstream (may call this skill)

| Upstream skill | Why it routes here |
| -------------- | ------------------ |
| `claims-file-reviewer` | A reviewer working the claim file finds a denial to appeal and wants the package assembled |
| `policy-document-explainer` | The member understood the policy and now wants to act on a denial |

## Do not conflate

| Adjacent skill | Difference |
| -------------- | ---------- |
| `claims-fraud-referral-assistant` | Fraud referral is a different, adverse workflow — not member appeal support |
| `claim-readiness-checker` | Pre-submission completeness of a claim not yet denied — this skill is post-denial |
| `claims-triage-assistant` | First-line claim intake/triage for the insurer, not member-side appeal drafting |

## Duplicate-execution prevention

- This skill computes the **evidence map, deadline, and argument scaffold only**; it must not
  file, submit, decide coverage, or give legal advice — those belong to the plan's appeal
  process, an external reviewer, or a licensed attorney.
- Downstream actors reuse the `appeal_id` package rather than recomputing it; the package is
  delivered by a human, never auto-submitted.
