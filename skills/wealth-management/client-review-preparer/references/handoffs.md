# Adjacent-Skill Handoffs — client-review-preparer

This skill is **pre-meeting preparation only**. It assembles a source-cited review pack
(brief, agenda, deck outline) and surfaces routing flags; it never recommends, decides,
trades, delivers, or writes a system of record. Every route below is a *surfaced suggestion
for a licensed human* — this skill takes none of these actions itself.

## Downstream / adjacent (this skill surfaces routes to)

| Skill | When | Handoff artifact |
| ----- | ---- | ---------------- |
| `investment-recommendation-evidence-reviewer` | A product/allocation change or any recommendation is contemplated | `client_id` + review pack + the contemplated change (evidence only) |
| `portfolio-rebalancing-assistant` | Allocation drift indicates a possible trade list (R4; advisor + client authorization) | `client_id` + drift context |
| `senior-investor-protection-screener` | Senior-investor / diminished-capacity / exploitation indicator | `client_id` + surfaced indicator |
| `household-financial-planning-assistant` | A life event or question requires re-checking goal progress | `client_id` + goals + life-event evidence |
| `retirement-income-scenario-modeler` | The meeting needs retirement-income / withdrawal scenarios | `client_id` + goals + assumptions |
| `investment-policy-statement-builder` | The IPS must be drafted or refreshed | `client_id` + objectives/constraints |
| `portfolio-proposal-comparator` | Two or more portfolio proposals must be compared | `client_id` + proposals |
| `wealth-lending-liquidity-reviewer` | Funding alternatives or pledged-asset risks need review | Actual household scope, dated cash need, debt and supplied terms; preserve unknowns |
| `private-market-client-reviewer` | Private commitments or cash obligations need reconciliation | Actual household/account scope, notices, settlements, manager artifacts and unresolved findings |
| `family-wealth-governance-preparer` | A family council, succession or next-generation discussion needs preparation | Reviewed family-group scope, sourced objectives and audience permission; household records are not automatically shareable |
| `trust-administration-reviewer` | A specific trust requires obligation, distribution or accounting review | Reviewed trust scope, actual account/beneficiary links, governing evidence and unresolved issues |
| `advisor-follow-up-assistant` | **After** the meeting: follow-up notes, actions, client comms, CRM updates | approved meeting outcomes |

## Human / specialist handoffs (no catalog skill — route to a person)

- **Licensed advisor and supervisory principal** adjudicate the pack, make any recommendation,
  and authorize any trade or delivery. This skill drafts; they decide.
- **Tax and legal questions** go to the client's own tax professional / attorney — never
  answered as advice here.

## Upstream (feeds this skill)

The wealth CRM, portfolio accounting/custody, performance, planning engine, and disclosure
library provide the read-only inputs. This skill is **interactive**
(`aws-fsi-scheduled-agent: no`); it is invoked to prepare a specific review, not on a schedule.

## Duplicate-execution prevention

- This skill **does not** analyze goal progress, model retirement income, build the IPS,
  compare proposals, review suitability, prepare or execute trades, or draft post-meeting
  follow-ups — each belongs to the named skill or a licensed human.
- It emits a `client_id`-keyed pack with `reviewer_signoff_required` and a recorded
  `approvals` block; downstream skills and the advisor consume that pack rather than
  re-preparing it.
- Routing flags are **surfaced for a human**, never auto-actioned.

A book-level review from `advisor-book-of-business-reviewer` can identify a due meeting, but it is not household meeting evidence. Map the actual household ID and source-linked history into this package; never use a `book:<book_id>` collection marker as `client_id`. Retain the originating book/action IDs and relevant unresolved concerns.
