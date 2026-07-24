# Adjacent-Skill Handoffs — security-master-enricher

This skill produces a security-master **enrichment pack** — PROPOSED enriched values with
provenance, plus a classified steward **conflict queue** (durable `enrichment_id`) — then
stops. It does not reconcile internal-vs-vendor values field-by-field, monitor feed data
quality, normalize positions/transactions, ingest raw sources, work valuation exceptions, or
create/merge anything in the security master.

## Upstream (may feed this skill)

| Upstream skill | Provides | Handoff artifact |
| -------------- | -------- | ---------------- |
| `investment-source-ingester` | Entitled, deduplicated, timestamped source observations (permission-classified) | Indexed source set the enrichment joins |
| `holdings-transaction-normalizer` | Canonical position/transaction records that reference the securities being enriched | Canonical records + `security_key`s |

## Downstream / route the human/reviewer to

| Skill | When (route instead of enriching here) | Handoff artifact |
| ----- | -------------------------------------- | ---------------- |
| `investment-vendor-feed-reconciler` | The task is comparing **internal vs an external vendor** value field-by-field (prices, ratings, index constituents, corporate-action terms, instrument attributes) with as-of times — not joining approved sources to propose a master value | `enrichment_id` + the conflicting fields |
| `investment-data-quality-exception-detector` | The task is **monitoring feed data quality** (stale prices, absent factors, duplicate instruments, implausible moves, broken mappings) and building a prioritized exception queue | `enrichment_id` + flagged records |
| `valuation-exception-packet` | The conflict is a **price / valuation** exception (stale, missing, disputed, outlier price) needing a cited valuation packet | `enrichment_id` + the security + price observations |

## The hard boundary — creating a security / resolving an identity (human steward)

There is **no catalog skill that creates a production security or resolves an identity**, by
design. `identifier_conflict` and `identifier_invalid` items, and any proposal a steward
approves, are actioned by an **authorized security-master steward (data governance) in the
security master** under segregation-of-duties controls. This skill hands over the proposals,
provenance, and conflict queue; the review, identity decision, and creation/write happen
outside it.

## Not this skill (route elsewhere)

- **Position / cash / transaction normalization** (custodian, administrator, OMS, accounting
  schemas → canonical schema) → `holdings-transaction-normalizer`, not reference-data
  enrichment.
- **Internal-vs-vendor field reconciliation** with as-of discrepancies →
  `investment-vendor-feed-reconciler`.

## Duplicate-execution prevention

- This skill **joins, proposes, and queues conflicts only**; it must not create securities,
  resolve/merge identities, adjudicate which source is canonical, or suppress a data-quality
  exception — those belong to the steward and the downstream skills.
- Downstream skills reuse the `enrichment_id`, proposals, provenance, and conflict queue rather
  than re-joining the sources.
