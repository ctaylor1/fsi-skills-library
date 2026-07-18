# Adjacent-Skill Handoffs — transaction-process-tracker

Process **tracking** (this skill) is separate from process **decisions** (bid selection,
exclusivity, go/no-go) and from process **execution** (sending outreach, executing NDAs,
granting data-room access, delivering materials). Those are human or operational actions.
This skill maintains a draft, source-linked tracker and surfaces exceptions; it does not
decide or act.

## Upstream (feeds this skill)

| Upstream skill | Provides | Handoff artifact |
| -------------- | -------- | ---------------- |
| `buyer-investor-list-builder` | The vetted counterparty universe to run outreach against | party list (ids, type, tiering) |
| `investment-banking-pitch-builder` | The mandate/pitch context that launches the process | approved process scope |

## Downstream / adjacent (this skill hands off to)

| Skill | When | Handoff artifact |
| ----- | ---- | ---------------- |
| `due-diligence-packager` | Diligence/data-room materials must be assembled or indexed for a party | `process_id` + party stage + diligence open items |
| `lbo-model-builder` | A sponsor bid must be valued/tested | `process_id` + bid reference (no selection) |
| `merger-model-builder` | A strategic/stock bid must be modeled | `process_id` + bid reference |
| `dcf-modeler` | Intrinsic valuation is needed to frame a bid | target reference (no recommendation) |

The tracker passes a bid *reference* for analysis; it never ranks or selects bids.

## Human / operations handoffs (no catalog skill — route to a person)

- **Sending outreach, executing/countersigning NDAs** → legal counsel and the deal-team
  coordinator (operational actions; the tracker only records the resulting status).
- **Granting or revoking data-room access** → the data-room administrator.
- **Bid selection, exclusivity, go/no-go** → the deal team lead / managing director.
- **Conflicts clearance and delivery approval** → the governance / compliance approver.
- **Delivering the tracker externally** → the named human owner, after approval.

## Duplicate-execution prevention

- This skill **does not** value targets, assemble diligence content, select bids, or execute
  process steps — those belong upstream, downstream, or to a human.
- The tracker emits a durable `process_id` and a versioned snapshot; consumers reference that
  snapshot rather than re-deriving process state.
- Control exceptions are **surfaced for human resolution**, never auto-resolved or advanced.
