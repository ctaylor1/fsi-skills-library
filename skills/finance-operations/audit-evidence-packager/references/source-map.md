# Source Map — audit-evidence-packager

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **GRC / audit-workpaper + evidence repository** | Request-to-artifact mapping, chain of custody, prior workpapers (system of record) | Read-only |
| 2 | **ERP/GL + subledgers** | Underlying financial artifacts (reconciliations, JE logs, balances) and their dates | Read-only |
| 3 | **Consolidation / FP&A** | Consolidated and management-reporting artifacts referenced by requests | Read-only |
| 4 | **Regulatory-reporting systems** | Regulatory-report extracts and validation evidence | Read-only |
| 5 | **Document intelligence (redaction)** | Redaction of flagged sensitive fields; page/field citation | Read-only |
| 6 | **Case management (chain of custody)** | Preparer, extraction timestamp, checksum, transfer/redaction actions | Read-only |
| 7 | Approved **remediation config** (versioned) | Open-item owner / target-date / severity mapping | Read-only |

The GRC/audit-workpaper repository is the **system of record** for request-to-artifact mapping
and custody. The ERP/GL and subledgers are authoritative for the underlying financial artifacts.
The remediation config is a **versioned contract** and is recorded on every package for
reproducibility.

## Citation format

`{source_system}:{source_ref}@{as_of_date}` — e.g. `erp-gl:recon=BR-OPS-2026-06@2026-06-30`,
`hcm:report=PAY-REG-2026-06@2026-06-30`, `iam:review=PAR-2026-H1@2026-06-15`.
Every request's readiness status must cite the artifact(s) it rests on.

## Freshness / effective dates

- Each artifact carries an `as_of_date` (or a `period`); period coverage is computed against the
  request's `period` relative to the engagement `audit_period` (see
  [domain-rules.md](domain-rules.md)).
- An artifact whose coverage date falls outside the requested period, or that is `superseded_by`
  a newer artifact, is treated as **stale** and surfaced for refresh — never quietly counted as
  current.
- Undatable evidence is treated as stale (cannot confirm period coverage).

## Least-privilege operations (deployment)

- `grc.requests(engagement)`, `grc.artifacts(request_id)`, `grc.custody(artifact_id)` — read-only
  request/artifact/custody pull.
- `erp.report(artifact_ref)`, `subledger.extract(ref)`, `consol.report(ref)`,
  `regreport.extract(ref)` — read-only artifact retrieval.
- `docintel.redact(artifact_id, fields)` — produces a redacted *copy* + redaction log; the source
  of record is never altered.
- `config.get('audit-remediation', version)` — read-only.
- No mutation from this skill. The assembled package is a **draft** handed to the audit
  coordinator / control owner; any delivery, sign-off, attestation, or system-of-record write is a
  separate, human-authorized action outside this skill.
