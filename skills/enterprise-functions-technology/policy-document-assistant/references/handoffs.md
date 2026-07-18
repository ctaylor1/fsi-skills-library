# Adjacent-Skill Handoffs — policy-document-assistant

Drafting a controlled policy is a **separate activity** from mapping regulatory obligations,
analyzing policy-to-regulation gaps, and packaging a policy for a committee or examiner.
Those have different inputs, entitlements, and reviewers. This skill assembles the draft +
source mapping + change summary and hands off; it does not perform the adjacent work itself.

## Upstream (feeds this skill)

| Upstream skill | Provides | Handoff artifact this skill consumes |
| -------------- | -------- | ------------------------------------ |
| `regulatory-change-impact-analyzer` | A regulatory change mapped to affected policies, controls, and owners with effective dates | The obligations/effective dates that seed new or amended requirements |
| `policy-procedure-gap-analyzer` | Identified gaps, conflicts, and obsolete steps in an existing policy/procedure | The gap list the draft is written to close |
| `contract-obligation-extractor` | Obligations, rights, and data terms extracted from contracts | Contractual obligations that become policy requirements |

## Downstream / adjacent (this skill hands off to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `policy-procedure-gap-analyzer` | To independently check the drafted policy against regulations, standards, and actual operations | Draft + source mapping |
| `board-committee-pack-builder` | The approved policy needs a controlled decision pack for a board/committee | Approved draft + change summary + approvals |
| `regulatory-exam-response-packager` | An examiner/inquiry requests the policy as evidence | Approved policy version + source mapping + approval record |
| `knowledge-base-curator` | After approval, stale/duplicate knowledge content must be updated or retired | Policy ID + new version + retirement candidates |

## Human / operations handoffs (no catalog skill)

- **Owner, legal, and compliance approval** of the draft — recorded by the human approvers,
  not by this skill.
- **Publication / activation** of the approved policy into the policy management system of
  record, and setting the real effective date — a controlled, human/operations action. This
  skill never publishes, activates, or files.
- **Licensed legal interpretation** of what a law requires beyond the approved requirements —
  routed to qualified legal counsel, not produced here.

## Duplicate-execution prevention

- This skill **does not** perform regulation-vs-policy gap analysis, regulatory-obligation
  mapping, contract obligation extraction, or committee/exam packaging — those belong to the
  skills above.
- Downstream consumers use this skill's draft, source mapping, and change summary rather than
  re-drafting the policy.
- The draft carries a proposed version and a `ready-for-review` state; only humans record
  approvals and activate — there is no autonomous publish path to duplicate.
