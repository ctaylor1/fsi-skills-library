# Adjacent-Skill Handoffs — nav-preparation-tie-out

This skill produces a NAV tie-out packet with a classified break list, lineage, and
**proposed-only** resolutions (durable `tie_out_id`), then stops. It does not strike NAV,
choose a price, post an accounting entry, adjudicate which source is correct, or resolve
subledger/valuation exceptions to disposition.

## Downstream (route the human/reviewer to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `valuation-exception-packet` | A `price_break` (stale, missing, disputed, or outlier price) needs valuation investigation and evidence | `tie_out_id` + the price break rows and observed prices |
| `position-cash-reconciliation-assistant` | The task is a **position/cash-only** reconciliation to custodian/prime-broker/administrator, not a full NAV tie-out | `tie_out_id` + the position/cash break rows |
| `investment-vendor-feed-reconciler` | The disagreement is an internal-vs-vendor **reference-data / attribute / rating** discrepancy, not a NAV component break | the instrument keys + field-level differences |
| `investment-data-quality-exception-detector` | A break is really a **feed data-quality** issue (stale, duplicate, broken mapping) needing a triage queue | `tie_out_id` + the affected break rows |
| `trade-break-resolver` | A quantity/position break traces to an **unmatched order/trade**, not a booking timing difference | the security key + position break rows |

## Upstream (may provide inputs / call this skill)

- `holdings-transaction-normalizer` normalizes custodian/administrator/OMS/accounting feeds
  into the canonical schema this skill consumes; wire it before the tie-out at deployment.
- `month-end-close-orchestrator` (Finance & Operations) may sequence a NAV tie-out as a close
  task and consume the `tie_out_id` and tie-out status. The orchestrator — not this skill —
  gates any eventual posting.

## Striking NAV, choosing a price, and posting (human / authorized system)

By design there is **no catalog skill that strikes NAV, selects a price, or posts an
accounting entry.** Those are authorized human/system actions under segregation-of-duties
controls:

- **NAV strike / certification** → the fund accountant / valuation committee in the accounting
  system.
- **Price selection / override** → the valuation control owner, evidenced via
  `valuation-exception-packet`.
- **Posting an adjustment** → an authorized fund accountant in the accounting system.

This skill hands over the tie-out, classified breaks, lineage, and `PROPOSED` resolutions; the
decisions and writes happen outside it.

## Duplicate-execution prevention

- This skill **classifies and evidences breaks and proposes resolutions only**; it must not
  strike NAV, choose a price, post an entry, adjudicate which source is correct, or approve its
  own resolutions — those belong to the human reviewer and the downstream skills.
- Downstream skills reuse the `tie_out_id`, breaks, and lineage rather than recomputing the
  match.
