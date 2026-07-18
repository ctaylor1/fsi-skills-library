# Adjacent-Skill Handoffs — buyer-investor-list-builder

List construction (this skill) is a **separate control activity** from conflicts clearance,
deal-process execution, and client delivery. This skill emits a durable `list_id`, a cited
source index, tiered outreach waves, and a conflicts-hold list; it must not perform the
downstream work.

## Upstream (feeds this skill)

| Upstream skill | Provides |
| -------------- | -------- |
| `company-profile-builder` | Candidate/target profiles that anchor fit rationale |
| `market-landscape-researcher` | The universe of players, competitors, and sponsors to seed candidates |
| `comps-analysis-builder` | Peer and precedent-transaction context supporting fit rationale |
| `due-diligence-packager` | Data-room extracts that anchor strategic-fit claims |
| `coverage-meeting-preparer` | Relationship history and coverage context |

These skills supply cited inputs; this skill scores, tiers, and screens them into a list.

## Downstream (this skill routes to)

| Downstream skill / owner | When | Handoff artifact |
| ------------------------ | ---- | ---------------- |
| `conflicts-of-interest-reviewer` | Any `hold-conflicts-review` candidate (restricted list or unresolved conflict) | `list_id` + candidate + restricted/conflict evidence |
| `transaction-process-tracker` | Approved list moves to outreach, NDA, access, and deadline tracking | `list_id` + approved outreach waves |
| `investment-banking-pitch-builder` | The approved buyer universe feeds process/pitch pages | `list_id` + cited buyer list |
| **Human deal team (MD / deal lead)** | Client delivery of the list and actual buyer outreach | Approved list draft (delivered by a human, never by this skill) |

Conflicts clearance and client delivery are **human/specialist** actions. This skill never
clears its own holds and never contacts a buyer.

## Duplicate-execution prevention

- This skill **does not** clear conflicts, execute outreach, track the deal process, or build
  pitch pages — those belong to the downstream owners above.
- A `duplicate` candidate is **linked** to its prior outreach-list entry for human confirmation;
  it is not re-listed in a wave or silently merged.
- Downstream owners consume the `list_id` and the approved waves rather than rebuilding the list.
