# Domain Rules - network-rules-change-tracker

How the monitor evaluates card-network / payment-scheme bulletins across **authenticity,
mapping, ownership, readiness,** and **freshness**, and maps results to alert severity. **Every
band, trusted-publisher set, and lead time is versioned configuration** owned by the payments
risk function (`config_version`); values are never hard-coded here, never inferred from a
bulletin, and never tuned per-bulletin. Orientation references: each network's operating
rules/bulletins (Visa, Mastercard, Nacha, RTP, and similar), the firm's change-management
standard, and its inventory/owner registries take precedence over anything in this file.

## Check taxonomy

| `category` | Scope | Fires (default config) | Evidence attached |
| ---------- | ----- | ---------------------- | ----------------- |
| `authenticity` | bulletin | Publisher not in trusted `networks`, or `signature_verified` != true, or missing `version`/`source_ref` | bulletin id, network, reason |
| `mapping` (`unmapped_domain`) | obligation | A declared `domain` has no impacts in the matching inventory category (completeness gap) | obligation id, unmapped domains |
| `mapping` (`dangling_reference`) | obligation | A referenced impact id is absent from the inventory of record (applicability gap) | obligation id, dangling refs |
| `ownership` (`no_owner`) | obligation | Obligation has no assigned `owner` | obligation id |
| `ownership` (`unknown_owner`) | obligation | `owner` is not in the owner registry | obligation id, owner |
| `readiness` | obligation | Days-to-effective within a band and `implementation.status` != complete | effective date, days, status |
| `freshness` | feed | `feed_as_of` older than `max_feed_staleness_days` | feed_as_of, staleness |

## Readiness bands (`breach_type`)

`days_to_effective = effective_date - as_of`. A `complete` obligation never fires. Otherwise:

| Band | Condition (default bands: critical<=30, high<=60, medium<=120) | Status |
| ---- | ------------------------------------------------------------- | ------ |
| `overdue` | `days_to_effective < 0` | BREACH |
| `critical` | `0 <= days_to_effective <= critical` | BREACH |
| `high` | `critical < days_to_effective <= high` | WARN |
| `medium` | `high < days_to_effective <= medium` | WARN |
| (on plan) | `days_to_effective > medium` | PASS (no alert) |

Band edges classify to the tighter band (`<=`). `required_lead_days` (or run `min_lead_days`) is
carried as evidence for the reviewer; it does not change the firing band.

## Severity mapping (deterministic, documented)

Severity is a triage suggestion, computed from `(category, status, breach_type)` - see
`expected_severity` in `scripts/calculate_or_transform.py` and re-derived in
`scripts/validate_output.py`:

| Severity | Category / condition | Routed queue |
| -------- | -------------------- | ------------ |
| **High** | Any `authenticity` alert, **or** a `readiness` `overdue` / `critical` BREACH | `network-rules-escalation` |
| **Medium** | Any `mapping` / `ownership` BREACH, **or** a `readiness` `high` WARN | `network-rules-review-queue` |
| **Low** | A `readiness` `medium` WARN, **or** a `freshness` flag | `network-rules-watchlist` |

Severity and queue are fully determined by the category, status, and band; they are never
adjusted by hand for a specific bulletin, network, or owner.

## Deduplication

Each result has a stable `fingerprint` = `bulletin_id|obligation_id|category|breach_type`
(obligation id is blank for bulletin-level authenticity/freshness). The run compares fingerprints
to the `open_alerts` baseline: matches are marked `is_duplicate` and routed to **still-open** (not
re-raised as new); everything else is **new**. This keeps a persistent gap (e.g., a still-overdue
obligation) from re-alerting every scheduled run while still recording that it remains open.

## Hard boundaries (fail closed)

- **Alert only.** Never adopt a rule; accept, close, file, or attest an obligation; change a
  procedure/control/contract/system; mark a change done; grant a waiver; or close/suppress an
  alert. Those are human payments compliance / product / operations actions.
- **No band / owner / mapping invention or tuning.** Use only the versioned config and inventory
  of record; if a band, trusted network, owner, or inventory item is missing or ambiguous, report
  the gap rather than guessing.
- **No determination or advice.** Describe a change factually (obligation, date, mapping, days);
  do not assert compliance/non-applicability, nor advise a specific way to comply.
- **No silent staleness or unverified sourcing.** If the feed is stale, flag it (`stale_input`);
  if a bulletin is unauthenticated, flag it (`unverified_source`); never present either as
  current/in-force or drop it.
