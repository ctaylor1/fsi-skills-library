# Domain Rules — relationship-manager-client-briefer

Orientation: commercial relationship management and portfolio coverage practice. The firm's
credit, covenant, pricing, and data-classification policies take precedence and are versioned
contracts. This skill **surfaces** relationship facts for a human RM; it makes no decisions.

## Assembly statuses (deterministic, precedence order)

A client record is assembled into exactly one status; earlier statuses take precedence.

| Order | Status | Condition |
| ----- | ------ | --------- |
| 1 | `needs-data` | Missing `legal_name`, `relationship_manager`, or any `exposures` (relationship summary incomplete). Not guessed. |
| 2 | `unresolved-entity` | `entity_resolved` is false. Client identity must be confirmed by a human; never guess who the client is. |
| 3 | `unsupported-content` | A content item cites a `source_id` not in the client's source inventory. The item is not carried. |
| 4 | `stale-source` | A cited source is older than its freshness threshold and not `stale_ack`. Not packaged until refreshed/acknowledged. |
| 5 | `draft-brief` | All invariants hold; the brief is assembled from the approved template with a citations index. Packageable. |

## Freshness thresholds

- **Critical content** — `exposures`, `covenants`, `profitability` — uses
  `critical_freshness_days` (default **10**). Credit/covenant/return context goes stale fast.
- **All other content** uses `freshness_days` (default **30**).
- `stale_ack: true` on a source marks an intentionally historical figure (e.g., a prior-year
  metric) so it records its age without blocking assembly.

## Exposure tie-out (deterministic)

- `total_committed` = sum of facility `committed`; `total_outstanding` = sum of facility
  `outstanding`; `utilization_pct` = 100 × outstanding / committed (0 if committed is 0).
- The output validator recomputes these and fails closed on any mismatch. Exposure figures
  are reported, not modeled or projected.

## Surfaced flags (never adjudicated here)

| Signal | Behavior |
| ------ | -------- |
| Covenant `breached` | Listed and flagged; routed to `covenant-compliance-monitor` / credit-risk review. The brief never waives, cures, or clears a covenant. |
| Covenant `at-risk` | Listed and flagged for monitoring. |
| Adverse news (`adverse: true`) | Listed and flagged; routed to `adverse-media-investigator`. The brief draws no financial-crime or reputational conclusion. |
| Overdue open action (`status=open`, `due_date < as_of_date`) | Marked `overdue: true` for the RM to address; not closed, reassigned, or rescheduled. |

## Cross-sell framing

Cross-sell items are **internal, sourced talking points** for the RM to weigh — never
personalized investment, financial, or tax advice to the client, and never a pricing or
product commitment.

## Hard boundaries (fail closed)

- No **delivery / send / submit / file** of the brief and no **CRM / system-of-record write**.
- No **credit, covenant, pricing, or risk-rating decision or commitment**.
- No **investment, legal, or tax advice**.
- No **fabrication** — every line needs a cited source; unsourced content is stripped.
- No **guessing client identity** — an unresolved entity blocks assembly.
- No **adjudication of adverse media** — surface and route only.

## Brief — required contents

Client identifiers; exposure summary with tie-out; covenant status (surfaced); profitability;
product holdings; service issues/open cases; recent news/media (adverse flagged); pipeline;
key contacts; cross-sell context (options, not advice); open actions (overdue flagged);
routing flags; a citations index for every item; recorded required approvals and the reviewer
sign-off block; the `as_of_date` and template version.
