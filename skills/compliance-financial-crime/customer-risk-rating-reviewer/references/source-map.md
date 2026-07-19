# Source Map — customer-risk-rating-reviewer

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **KYC/AML case** system (record) | Rating of record, scored risk factors, documented overrides | Read-only |
| 2 | Methodology **config** (versioned) | Factor catalog, weights, band thresholds, mandatory floors, staleness window | Read-only |
| 3 | **Sanctions/PEP screening** | PEP status and potential sanctions nexus behind the geography/ownership factors (potential indicators only) | Read-only |
| 4 | **Transaction-monitoring** + **adverse-media** | Trigger events (alerts, adverse media) that may warrant a re-rating | Read-only |
| 5 | **Records archive** | Prior periodic reviews, prior override approvals, effective dates | Read-only |

The KYC/AML case system holds the rating of record and factor values; the methodology config
is the **rule contract** for how factors combine into a band. Screening/monitoring/adverse-media
sources contribute **potential indicators only** — never a disposition. A customer or
relationship-manager assertion never overrides the record, the registry, or the methodology.

## Citation format

`{system}:{ref}@{date}` — e.g. `kyc:cust=****4021;factor=geography@2025-11-15`,
`kyc:cust=****4021;override=OV-3120@2025-06-01`, `tm:cust=****4021;trigger=TR-8801@2026-06-20`.
Missing-factor findings cite the methodology contract:
`methodology:crr-methodology-2026.06;required_factor=sanctions_nexus`. Every finding cites the
specific record row (or the methodology) behind it.

## Freshness / effective dates

- The methodology (factor catalog, weights, thresholds, floors) is a **versioned contract**;
  the output records the `methodology_version` used so a review is reproducible.
- Each factor carries an `observed_date`; a factor older than the staleness window (default
  365 days) is flagged `stale_factor` but still used, with a warning to refresh.
- Overrides carry `approved_date` and `expiry_date`; an override past its expiry as of the
  review date is `expired_override`.
- Trigger events carry a `date`, `severity`, and `assessed` flag.

## Least-privilege operations (deployment)

- `kyc.rating(customer_id)` → rating of record + effective date + source_ref.
- `kyc.factors(customer_id, methodology_version)` → scored factor rows.
- `kyc.overrides(customer_id)` → documented override rows (approver, rationale, dates).
- `config.get('crr-methodology', version)` → catalog, weights, thresholds, floors, staleness.
- `tm.triggers(customer_id, since)` / `adverse_media.hits(customer_id)` → trigger indicators.
All read-only, deterministic, durable `review_id`, below the fixed timeout; page long factor
histories as resumable stages. No write, disposition, or closure operation is bound.
