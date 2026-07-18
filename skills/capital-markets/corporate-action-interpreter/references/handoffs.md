# Adjacent-Skill Handoffs — corporate-action-interpreter

This skill produces a **normalized interpretation** of one corporate-action event and
stops. It does not elect, tender, compute tax, or reconcile. Upstream and downstream skills
exchange the durable `interpretation_id` (and the notice's `event_id`).

## Upstream (may call this skill / provide inputs)

| Upstream skill | Provides | Handoff artifact |
| -------------- | -------- | ---------------- |
| `portfolio-holdings-summarizer` | The eligible position (quantity + as-of) to size entitlements | `snapshot_id` + normalized position |
| Operations queue / notice intake | The authoritative depository/agent/issuer notice | `event_id` + notice reference |

## Downstream (this skill hands off to)

| Downstream skill / owner | When to route | Handoff artifact |
| ------------------------ | ------------- | ---------------- |
| `corporate-action-election-assistant` (R4) | Holder wants to actually elect / tender / subscribe | `interpretation_id` + chosen option (decided by a human, not here) |
| Licensed tax professional (no catalog skill) | Personalized tax result, cost-basis restatement, lot/wash-sale treatment | `interpretation_id` + event terms |
| Corporate-actions operations team (no catalog skill) | Reconcile received entitlements vs. announced after pay date | `interpretation_id` + expected entitlements |
| Corporate-actions operations exception queue (no catalog skill) | Ambiguous, contradictory, or superseded terms flagged for review | `interpretation_id` + `ambiguities[]` |

## Duplicate-execution prevention

- This skill **only interprets and computes entitlements**; it must not elect, tender,
  compute personalized tax, or reconcile received vs. announced — those belong to the
  downstream skills and owners above.
- Downstream owners must **not** re-parse the notice or re-derive entitlements when a valid
  `interpretation_id` for the same event and position already exists; they reuse it.
- The chosen election option is always decided by a **human** (or the R4
  `corporate-action-election-assistant`'s approval gate); this skill never selects or
  records one.
