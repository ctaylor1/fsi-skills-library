# Adjacent-Skill Handoffs — investment-data-quality-exception-detector

This skill produces a cited, prioritized **exception queue** (`exception_queue_id`) and
stops. It does not reconcile disagreements, enrich the security master, correct data, or
close exceptions.

## Downstream (route each exception to)

| Downstream target | When | Handoff artifact |
| ----------------- | ---- | ---------------- |
| `investment-vendor-feed-reconciler` | A `conflicting_classification` (or any approved-source disagreement on price/rating/index/attribute) needs field-level reconciliation | `exception_id` + the conflicting feed rows |
| `security-master-enricher` / security-master steward | A `duplicate_instrument` or `broken_mapping` needs identity resolution, a new/merged record, or a fixed mapping | `exception_id` + colliding keys / unresolved target |
| `investment-data-analyst-review` (human, with the source owner) | `stale_price`, `implausible_move`, `absent_factor` — the analyst confirms with the pricing/analytics owner | `exception_id` + evidence |

Downstream skills also do not choose a canonical value on their own:
`investment-vendor-feed-reconciler` produces field-level discrepancies and routes price
exceptions onward; `security-master-enricher` proposes enrichment for steward approval.

## Upstream (produces this skill's input)

| Upstream | Role |
| -------- | ---- |
| `holdings-transaction-normalizer` | Normalizes custodian/administrator/OMS/accounting records into the canonical snapshot this detector reads. Run it first when the feed is not yet canonical. |

## Duplicate-execution prevention

- This skill **detects and evidences** exceptions only; it must not reconcile, enrich,
  correct, suppress, or close — those belong to the downstream skills and the human owner.
- Downstream skills consume the referenced `exception_id` items rather than re-detecting, so a
  given snapshot is swept once and worked once.
- `exception_queue_id` and `exception_id` are durable for a given snapshot + `config_version`,
  preventing double-queuing of the same finding.
