# Source Map — data-loss-prevention-incident-assistant

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **DLP console / SIEM-SOAR** | DLP event + case state (system of record), triggering signal ids, correlation, durable `case_id` | Read-only |
| 2 | **IAM / identity** | Actor resolution, privilege level, department, entitlements | Read-only |
| 3 | **CMDB / asset inventory** | Endpoint/asset resolution, managed state, ownership | Read-only |
| 4 | **Web / mail / egress proxy** | Destination resolution, trust category, egress confirmation | Read-only |
| 5 | **Threat intelligence** | Destination/domain reputation, active-exfiltration indicators | Read-only |
| 6 | **Data classification service / catalog** | Detected data types, record counts, sensitivity mapping | Read-only |
| 7 | **Incident & BCP systems** | Existing incidents, business-continuity context for routing | Read-only |
| 8 | Approved **suppression rule set** + **classification config** + **severity config** + **output template** (versioned) | Suppression, classification, scoring, template fidelity | Read-only |

Breach determination, notification-obligation analysis, incident declaration, identity/access
review, cloud-posture confirmation, and third-party risk review are **specialist / IR / privacy-
legal domains** (see [handoffs.md](handoffs.md)); this skill consumes their read-only signals as
enrichment and routes for confirmation rather than concluding.

## Citation format

`{system}:{ref}@{date/version}` — e.g. `dlp:event=DLP-4001@2026-07-17`,
`iam:identity=user-****-711@2026-07-17`, `cmdb:asset=AST-LT-77@2026-07-17`,
`proxy:dest=paste-site-external@2026-07-17`, `dlp:policy=DLP-BULK-PII@2026-07-17`,
`config:dlp-suppression@dlp-2026.07`. Every enriched signal carries at least one citation; an
uncited "present" evidence section is downgraded to an unsupported claim by
[../scripts/validate_output.py](../scripts/validate_output.py).

## Freshness / effective dates

- DLP event/case state and destination reputation must be read **fresh** — a stale IOC
  reputation or an already-escalated event invalidates the package.
- Actor/asset context is read from IAM/CMDB as-of the assessment time; the `as_of` date is
  recorded on every citation.
- The suppression rule set, classification config, severity config, and output template are
  **versioned contracts**; their versions are recorded on every package for reproducibility and
  review.

## Least-privilege operations (deployment)

- `dlp.events.read(queue|event_id)`, `dlp.cases.find(actor, rule, window)` (correlation) — read-only.
- `iam.identity(identity_ref)` → privilege, department, entitlements (read-only).
- `cmdb.asset(asset_id)` → managed state, ownership (read-only).
- `proxy.destination(dest_ref)` → trust category, egress confirmation (read-only; no block).
- `ti.lookup(destination|indicator)` → reputation / active-exfiltration flags (read-only; no disposition).
- `classification.lookup(event_id)` → detected data types, record counts (read-only).
- `config.get('dlp-suppression'|'dlp-classification'|'dlp-severity'|'dlp-incident-template', version)` — read-only.

No mutation from this skill. Assembling the package writes **nothing** to a system of record;
the package is a draft proposal for the human privacy/IR owner, recorded via the approval broker.
No DLP-console/case/ticket write, no containment action (block, quarantine, revoke, delete,
recall, account disable), and no notification is performed here.
