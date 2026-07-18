# Domain Rules — transaction-reporting-quality-checker

Deterministic transaction-reporting quality checks and how their exceptions map to a
**remediation-priority band**. Thresholds, required fields, and identifier formats are
**configuration** (versioned, owned by the regulatory-reporting control team), not hard-coded
judgments, and are never tuned to a single desk or day. The firm's reporting standard and the
applicable regime rules (e.g. MiFIR/RTS 22, EMIR, CFTC/SEC-style regimes) take precedence.

## Matching key

Reports are matched to reportable source executions on `transaction_ref`. Only executions
with `reportable: true` count toward completeness. A duplicate `transaction_ref` on either
side is surfaced as ambiguity, not silently paired.

## Exception taxonomy

| Code | Fires when | Severity | Evidence attached |
| ---- | ---------- | -------- | ----------------- |
| `missing_report` | A reportable source execution has no matching submitted report | blocking | Source exec row |
| `over_report` | A submitted report has no matching **reportable** source (no source, or source not reportable) | blocking | Report row |
| `economic_field_mismatch` | A configured economic field (default `instrument_isin`, `price`, `quantity`) on the report differs from the source beyond tolerance | blocking | Both sides + values |
| `invalid_identifier` | A populated identifier (LEI/ISIN/MIC) fails the configured format for its kind | high | Report field + value |
| `missing_required_field` | A configured mandatory field is empty/absent on the report | high | Report + field list |
| `late_report` | Submission timestamp − execution timestamp > `timeliness_deadline_hours` | high | Report + computed lag |
| `rejected_report_unresolved` | Report status is in `unresolved_statuses` (default rejected/pending/failed) | high | Report + status |
| `noncritical_field_mismatch` | A configured supplementary (non-economic) field differs from source | low | Both sides + values |

Exceptions are **additive and independent**; each fired exception is reported with its own
evidence. There is no opaque composite "quality score".

## Default config (versioned; override per regime/deployment)

| Key | Default | Meaning |
| --- | ------- | ------- |
| `timeliness_deadline_hours` | 24 | Max hours from execution to submission (T+1 style) |
| `required_fields` | firm LEI, buyer/seller IDs, ISIN, MIC, price, quantity, trade datetime, txn ref | Mandatory populated fields |
| `identifier_formats` | `lei`, `isin`, `mic` regexes | Format validity per identifier kind |
| `economic_fields` | ISIN, price, quantity | Fields reconciled to the source of record |
| `price_tolerance_abs` | 0.005 | Absolute tolerance for numeric economic comparison |
| `unresolved_statuses` | rejected, pending, failed | Statuses treated as unresolved |

Identifier checks here are **format** checks (regex). Check-digit validation (ISIN Luhn, LEI
mod-97) is a deployment enhancement wired at integration; record the reference-data snapshot.

## Priority mapping (deterministic, documented)

| Suggested band | Rule |
| -------------- | ---- |
| **Clean** | No exceptions fired |
| **Review** | Only low-severity exceptions fired |
| **High** | Any high-severity exception fired, no blocking |
| **Blocking** | Any blocking-severity exception fired (completeness gap or economic mismatch) |

Priority is a **triage suggestion for a human**. It is not a compliance determination and it
never triggers a report submission, amendment, cancellation, or suppression.

## Hard boundaries (fail closed)

- Never state or imply the firm **is** in breach, is non-compliant, or has committed a
  reporting violation — describe defects factually and attribute conclusions to the human.
- Never recommend or take a **report action** (submit / amend / cancel / resubmit / suppress)
  or a **self-report** to a regulator.
- Never decide a transaction **is not reportable**; reportability comes from the source.
- Never override the deterministic priority mapping.

## False-positive checks (always include when any exception fired)

Confirm no exemption / waiver / deferral applies; normalize timezones and cut-off calendars
before treating a report as late; confirm a correction is not already in flight before
treating a reject as unresolved; confirm the source-of-record field is itself correct before
treating a mismatch as a report defect; confirm the effective reference-data snapshot was used.
