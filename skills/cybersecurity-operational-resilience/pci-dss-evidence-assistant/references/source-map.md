# Source Map — pci-dss-evidence-assistant

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **PCI DSS standard + SAQ/ROC templates** (approved-source retrieval) | Requirement text, testing procedures, applicability, SAQ type | Read-only |
| 2 | **GRC / evidence repository** | Controls, control-to-requirement mapping, evidence artifacts, owners, dates | Read-only |
| 3 | **Vulnerability scanner** (ASV + internal) | Req 6/11 scan and penetration-test evidence and dates | Read-only |
| 4 | **Configuration / CMDB** | Req 1/2/6 network + system configuration evidence and CDE scope inputs | Read-only |
| 5 | **IAM / directory** | Req 7/8 access-review and least-privilege evidence | Read-only |
| 6 | **Ticketing / case management** | Remediation owners, target dates, exception records | Read-only |
| 7 | Approved **freshness-window + remediation config** (versioned) | Staleness thresholds; gap severity/owner mapping | Read-only |

The GRC/evidence repository is the **system of record** for control-to-evidence mapping.
The PCI DSS standard and SAQ/ROC templates are **versioned contracts** — pin the DSS version
(e.g., `4.0.1`) and the SAQ type. The freshness-window config is versioned and recorded on
every package for reproducibility.

## Citation format

`{source_system}:{source_ref}@{effective_date}` — e.g. `grc:review=NSC-2026-H1@2026-05-01`,
`vulnscan:asv=Q2-2026-PASS@2026-06-20`, `iam:review=ACC-2025-H2@2025-11-01`.
Every requirement's readiness status must cite the evidence it rests on.

## Freshness / effective dates

- Each evidence item carries an `effective_date`; staleness is computed against the
  per-type freshness window relative to the package `as_of_date` (see
  [domain-rules.md](domain-rules.md)).
- Undatable evidence is treated as **stale** (surfaced for refresh), never as fresh.
- Collection-recency thresholds are not a substitute for scan/test cadence, sample adequacy or assessment-period coverage.

## Least-privilege operations (deployment)

- `pcistd.get(requirement_id | saq_type, dss_version)` — read-only standard/template text.
- `grc.controls(scope)`, `grc.evidence(control_id)` — read-only control + evidence pull.
- `vulnscan.results(scope, from, to)`, `cmdb.config(scope)`, `iam.access_reviews(scope)` —
  read-only evidence retrieval.
- `config.get('pci-freshness'|'pci-remediation', version)` — read-only.
- No mutation from this skill. The assembled package is a **draft** handed to the PCI
  program manager; any submission, attestation, or system-of-record write is a separate,
  human-authorized action outside this skill.

## Verified orientation sources (2026-09-17)

- [PCI SSC FAQ 1154](https://www.pcisecuritystandards.org/faqs/1154/) identifies requirement 3.3.1 for SAD after authorization.
- [PCI SSC FAQ 1533](https://www.pcisecuritystandards.org/faqs/1533/) explains why the restriction applies even where no PAN is present.
- [PCI SSC document library](https://www.pcisecuritystandards.org/document_library/) provides versioned standards and assessor templates.

Read the applicable standard and testing procedures for the exact assessment; the offline code does not retrieve them.
