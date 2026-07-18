# Source Map — communications-compliance-reviewer

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Communications archive** (position of record) | The communication text, channel, audience, recipients, capture/retention status | Read-only |
| 2 | **Supervision / approval system** | Principal pre-approval, reviewer, review date, first-use date | Read-only |
| 3 | **Controlled content library** (WSPs, disclosure register) | Required disclosures, approved legends, current rule mappings, effective dates | Read-only |
| 4 | **Reference data** | Entity/rep resolution, security identifiers, channel taxonomy | Read-only |
| 5 | **Rulebook config** (versioned) | Classification thresholds, prohibited-claim library, disclosure requirements, disposition mapping | Read-only |

The communications archive is the record of what was said and to whom. Never substitute an
author's assertion for the archived communication. If the archive and the supervision system
conflict (e.g., archive shows first use before the recorded approval date), cite both and
flag for the reviewer — do not resolve silently.

## Citation format

`comm:{source_ref}@{as_of}` — e.g. `comm:comm=COMM-90001;sys=comm-archive@2026-07-16`. Every
finding cites the specific evidence (the matched text, the disclosure gap, or the
supervision/retention field) and where it was found (`body`, `disclosures`, `supervision`,
`retention`).

## Freshness / effective dates

- The rulebook config (classification thresholds, prohibited-claim library, disclosure
  requirements, disposition mapping) is a **versioned contract**; the output records the
  `config_version` used so a review is reproducible.
- Rule citations (FINRA 2210 / 3110, SEC 17a-4, FINRA 4511 / 4513 / 4530) are **orientation
  labels**. The firm's Written Supervisory Procedures (WSPs) and the current rule text govern;
  a jurisdiction pack configures non-US regimes.
- Communication classification depends on the recipient count within the configured window
  (default 30 days); state the count and window used.

## Least-privilege operations (deployment)

- `archive.get(comm_id)` → the communication text, channel, audience, recipient count, capture
  status.
- `supervision.get(comm_id)` → principal-approval and review metadata.
- `content.requirements(comm_class, channel)` → required disclosures + approved legends.
- `refdata.resolve(rep|security|channel)` → normalized values.
- `config.get('comms', version)` → thresholds, claim library, disposition mapping.

All read-only, deterministic, durable `review_id`, below the fixed timeout; page long
archives as resumable stages. No mutating tools: this skill never writes approval, files, or
closes a review.
