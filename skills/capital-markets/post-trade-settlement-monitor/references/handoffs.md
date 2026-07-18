# Adjacent-Skill Handoffs — post-trade-settlement-monitor

This skill produces a prioritized, deduplicated, freshness-stamped **alert queue** (`run_id`)
and stops. It does not investigate to root cause, repair, fund, dispute, or settle. Each
alert names a `suggested_route`; the human reviewer disposition-routes from the queue.

## Downstream (route the human/reviewer to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `trade-break-resolver` | The fail traces to a matching/economics break that needs investigation and repair | `run_id` + instruction/trade IDs + fail evidence |
| `margin-collateral-optimizer` | Aged fails / buy-in exposure create a funding or collateral shortfall to cover | instruction IDs + cash impact |
| `transaction-reporting-quality-checker` | The exception implies a regulatory transaction-reporting data-quality issue | instruction IDs + fields in question |
| `corporate-action-election-assistant` | The fail is driven by an unactioned corporate-action entitlement/mismatch | security + event reference |
| `trade-confirmation-explainer` | The reviewer needs the underlying confirmation explained, not an exception raised | trade ID |

## Human / operations handoffs (no skill — route to a person)

- **CSDR mandatory buy-in / penalty decisions**, at-fault determinations, and penalty
  disputes → the settlement-fails desk and CSDR penalties analyst (licensed/authorized
  operations decision, not a skill).
- **Counterparty, custodian, or CSD outreach** and instruction repair/resubmission →
  settlement operations (an entitled human action).
- **Funding / cash-management escalation** for large net fail impact → the funding desk.

Never invent a skill for these; they are human operations decisions the monitor only
*flags* and prioritizes.

## Upstream (may trigger this skill)

This is primarily a **scheduled** monitor (`aws-fsi-scheduled-agent: read-only-monitoring`);
its schedule and pre-cutoff sweeps trigger runs. Settlement-ops dashboards may also request
an on-demand run. It has no upstream skill that grants it any action entitlement.

## Duplicate-execution prevention

- The monitor **raises and prioritizes alerts only**; it must not investigate to disposition,
  repair, fund, dispute, close, or contact anyone — those belong to the human reviewer and
  the downstream skills above.
- Deduplication marks a repeat exception `duplicate` against already-open alerts so the same
  fail is not re-paged each run; the underlying exception stays open until a human resolves
  it. Downstream skills reuse the `run_id` evidence rather than recomputing alerts.
