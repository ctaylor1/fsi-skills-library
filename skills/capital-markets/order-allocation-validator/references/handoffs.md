# Adjacent-Skill Handoffs — order-allocation-validator

Produces a cited allocation-exception packet (`validation_id`) and stops. It does not
allocate, amend, book, or resolve breaks.

## Downstream (route the human/reviewer to)
| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `trade-break-resolver` | Quantity/trade break — proposed lines don't reconcile to executed fills | order id + break evidence |
| `best-execution-reviewer` | Execution-quality / venue-routing review (not allocation) | order id |

## Upstream (may call this skill)
Trade-support and trading-compliance workflows may request an allocation-validation packet.
This skill is interactive (`aws-fsi-scheduled-agent: no`).

## Duplicate-execution prevention
- This skill only **validates and evidences** the proposed allocation; it never allocates,
  amends, books, or resolves breaks — those belong to the human/OMS and `trade-break-resolver`.
- Downstream reuses the `validation_id` evidence rather than recomputing.
