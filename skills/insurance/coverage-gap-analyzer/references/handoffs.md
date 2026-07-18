# Adjacent-Skill Handoffs — coverage-gap-analyzer

This skill produces a cited **coverage-gap analysis** (`analysis_id`) with a suggested
review priority and stops. It does not explain the whole policy, compare quotes, decide
coverage, or draft customer-facing letters.

## Downstream (route the human/reviewer to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `policy-document-explainer` | The user just wants a plain-language walkthrough of the policy, not a needs-vs-terms gap analysis | policy + section |
| `policy-wording-comparator` | The question is whether form/endorsement **wording** matches an approved/filed form (R3, clause-level) | policy forms + endorsements |
| `premium-quote-comparator` | The user wants to compare priced quotes/options across carriers | normalized quotes |
| `policy-renewal-reviewer` | The task is comparing expiring vs. proposed terms at renewal and drafting renewal questions | expiring + proposed terms |
| `claim-readiness-checker` | An actual loss has occurred and the user needs claim-submission completeness | claim + evidence |
| `claim-denial-appeal-helper` | A claim was denied and the user needs appeal support | denial letter + policy |

## Upstream (may call this skill)

Producer/agent-desk and renewal skills may request a gap analysis to attach to a client
review. A scheduled monitor is **not** used here (`aws-fsi-scheduled-agent: no`); the related
`catastrophe-exposure-monitor` handles read-only exposure monitoring separately.

## Duplicate-execution prevention

- This skill computes and evidences **gaps only**; it must not determine coverage, advise a
  purchase, compare priced quotes, or draft a customer letter — those belong to the human
  professional and the downstream skills.
- Downstream skills reuse the `analysis_id` evidence rather than recomputing gaps.
