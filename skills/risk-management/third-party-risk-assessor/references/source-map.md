# Source Map — third-party-risk-assessor

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Third-party inventory / vendor register** (position of record) | Vendor identity, criticality tier, function, spend, subcontractor (fourth-party) disclosures | Read-only |
| 2 | **Control evidence & assurance repository** | Control status, last-tested dates, SOC 2 / ISO / pen-test evidence, remediation state | Read-only |
| 3 | **Risk register / limits / loss events / scenarios** | Concentration, appetite/limits, prior operational-risk events, resilience scenarios | Read-only |
| 4 | **Finance & operational data** | Vendor financial statements, credit ratings, SLA/uptime, RTO/RPO, exit-plan artifacts | Read-only |
| 5 | **Third-party-risk config** (versioned) | Dimension thresholds, critical control domains, elevated-risk jurisdictions, composite mapping | Read-only |

Never substitute a vendor's self-assertion for the control-evidence record or the vendor
register. If a self-attestation and the assurance repository conflict, cite both and flag for
the reviewer; do not resolve silently.

## Citation format

`{system}:{ref}@{date}` — e.g. `tpr:vendor=V-4471;ctrl=CTL-ENC-01@2026-07-15`. Every
material finding cites the specific evidence row(s) it derives from and the `as_of` date of
the assessment.

## Freshness / effective dates

- Config (thresholds, critical domains, jurisdiction list, mapping) is a **versioned
  contract**; the output records the `config_version` and `framework_version` used so an
  assessment is reproducible.
- Control evidence has a `last_tested` date; evidence older than `control_test_max_days` (or
  missing a date) is treated as a **gap**, not as passing.
- Financial statements carry a `statement_period`; state it and flag stale financials.
- The assessment reflects the vendor state **as of** the stated date; re-run when material
  inputs change (new subcontractor, incident, downgrade, contract change).

## Least-privilege operations (deployment)

- `vendor.get(vendor_id)` → inventory record, criticality, spend, subcontractor disclosures.
- `controls.evidence(vendor_id)` → control rows with status, last-tested, assurance refs.
- `riskreg.context(vendor_id)` → concentration, limits, linked loss events/scenarios.
- `finance.profile(vendor_id)` → financial ratios, rating, SLA/RTO, exit-plan artifacts.
- `config.get('third-party-risk', version)` → thresholds + critical domains + mapping.

All read-only, deterministic, with a durable `assessment_id`, below the fixed timeout; page
large control/subcontractor sets as resumable stages. No write, submission, or state change
is performed by this skill.
