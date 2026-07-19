# Source Map — third-party-cyber-risk-reviewer

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Vulnerability & cloud-posture** management (position of record for exposure) | Open critical/high findings, SLA breaches, oldest-open age | Read-only |
| 2 | **Incident & BCP** systems | Supplier incidents affecting our data, disclosure timeliness, resilience/RTO evidence | Read-only |
| 3 | **CMDB / entity resolution** | Supplier ↔ service mapping, criticality, data classification, internet exposure | Read-only |
| 4 | **IAM** | Supplier/fourth-party access to our data and systems | Read-only |
| 5 | Supplier **security evidence** (SIG/CAIQ questionnaire, SOC 2 / ISO 27001 reports, pen-test attestations) | Control coverage, certifications, subcontractor list, contractual terms | Read-only |
| 6 | **Threat intelligence** | Adverse events, breaches, exposure attributable to the supplier | Read-only |
| 7 | Third-party-risk **config** (versioned) | Finding thresholds, mandatory domains, residual-tier mapping | Read-only |

Supplier attestations (rank 5) are the supplier's own assertion; where an internal system of
record (ranks 1–4) contradicts an attestation, cite both and flag the conflict for the
reviewer — never resolve it silently in the supplier's favor.

## Citation format

`{system}:{ref}@{date}` — e.g. `vm:scan-2026-07@2026-07-15`, `soc2:2025-report@2026-03-31`,
`ir:INC-2026-08@2026-07-02`. Every fired finding cites the specific evidence rows and the
effective date behind them. Intake-only assertions (no external ref) cite `intake@{as_of}`
and are lower confidence.

## Freshness / effective dates

- Config (thresholds, mandatory domains, tier mapping) is a **versioned contract**; the
  output records `config_version` so a review is reproducible.
- Attestations carry a `valid_until`; an out-of-date or out-of-scope attestation reads as
  missing coverage, not as pass.
- Vulnerability and incident evidence must be dated; stale scans are flagged, not trusted.

## Least-privilege operations (deployment)

- `vuln.posture(supplier_id)` → open critical/high counts, SLA breaches, oldest-open age.
- `incident.list(supplier_id, since)` → incidents affecting our data + disclosure timeline.
- `cmdb.resolve(supplier_id)` → service mapping, criticality, data classification.
- `iam.access(supplier_id)` → supplier/fourth-party entitlements to our data.
- `evidence.get(supplier_id)` → questionnaire, attestations, subcontractor list, contract terms.
- `config.get('third-party-cyber', version)` → thresholds + residual-tier mapping.

All read-only, deterministic, durable `review_id`, below the fixed timeout; page long
evidence sets as resumable stages. No write, submission, or state change is ever made.
