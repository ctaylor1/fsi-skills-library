# Adjacent-Skill Handoffs — financial-document-version-comparator

Produces a change log (`comparison_id`) and stops. It does not judge significance, approve,
edit, or publish.

## Downstream / lateral (route to)
| Skill | When |
| ----- | ---- |
| `contract-obligation-extractor` | Extract obligations/terms from a contract (not just diff versions) |
| `communications-compliance-reviewer` | Compliance review of a research/communication draft |
| `policy-wording-comparator` | Comparing INSURANCE policy forms/endorsements specifically |

Judgments of materiality, legal significance, or disclosure sufficiency go to a licensed/legal
reviewer (human), never this skill.

## Upstream (may call this skill)
Deal-execution and document-control workflows request a version diff. Interactive
(`aws-fsi-scheduled-agent: no`).

## Duplicate-execution prevention
- This skill **locates changes only**; it never judges significance, approves, edits, or
  publishes — those belong to human/legal reviewers and document control.
- Downstream reuses the `comparison_id` change log rather than re-diffing.
