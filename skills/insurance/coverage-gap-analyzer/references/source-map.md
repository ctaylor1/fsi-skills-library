# Source Map — coverage-gap-analyzer

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Policy administration** (policy of record) | Coverages, limits, deductibles, sublimits, exclusions, endorsements, forms | Read-only |
| 2 | **Document intelligence** | Extract terms/limits/exclusions from the policy PDF, dec page, and endorsements with clause/page citation | Read-only |
| 3 | **Producer / needs-analysis systems** | Stated needs and exposures (assets, replacement cost, liability, life events) | Read-only |
| 4 | **Actuarial / catastrophe & reference data** | Peril taxonomy, geo/zone exposure (e.g., FEMA flood zone), replacement-cost benchmarks | Read-only |
| 5 | **Underwriting-rules / coverage config** (versioned) | Gap thresholds (deductible-burden ratio, tolerances) and priority mapping | Read-only |

The **policy of record** governs what is actually in force. Stated needs and exposures are
**client-provided and unverified** — treat them as inputs to analyze, never as coverage
facts. Where the dec page and an endorsement conflict, cite both and flag for the reviewer;
the effective endorsement generally controls but that determination belongs to a licensed
professional.

## Citation format

Every fired gap carries **two** citations:
- exposure side: `needs:{source_ref}@{as_of}` — e.g. `needs:needs=****4471;item=E-1@2026-07-15`
- policy side: `policy:{source_ref}` — e.g. `policy:pol=HO****-1234;form=HO-3;cov=A`

For a *missing* coverage or *missing* endorsement, the policy citation points at the
coverage schedule that lacks it (`policy:{policy_number}#coverage-schedule`).

## Freshness / effective dates

- The coverage config (thresholds, priority mapping) is a **versioned contract**; the output
  records `config_version` so an analysis is reproducible.
- Policy terms are read as of the policy's current effective period; state the `as_of` used.
- Exposure values change with life events and inflation — the output notes that values are
  client-stated and unverified.

## Least-privilege operations (deployment)

- `policy.get(policy_number)` → coverages, limits, deductibles, sublimits, exclusions, endorsements.
- `docintel.extract(policy_doc)` → terms + clause/page citations for the dec page & endorsements.
- `needs.get(profile_id)` → stated exposures (bounded; no free-text PII beyond what evidences a gap).
- `refdata.resolve(peril|zone)` → normalized peril taxonomy and geo/zone exposure.
- `config.get('coverage-gap', version)` → thresholds + priority mapping.

All read-only, deterministic, durable `analysis_id`, below the fixed timeout; page long
policy schedules as resumable stages.
