# Source Map — transaction-process-tracker

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | Deal / **process CRM** (deal-management) | Party list, stage, engagement, milestones (system of record for process state) | Read-only |
| 2 | **Contract / NDA management** (DMS / e-signature) | NDA sent / executed status and dates | Read-only |
| 3 | **Virtual data room (VDR)** | Data-room access grants, Q&A, document availability | Read-only |
| 4 | **Governance / approvals** system | Deal-committee, conflicts-clearance, and delivery approvals | Read-only |
| 5 | **Entity resolution / reference data** | Counterparty identity, sponsor vs. strategic classification | Read-only |
| 6 | **Prior tracker snapshot** (versioned) | Change-log diff base | Read-only |
| 7 | **Process config** (`stage_order`, `required_approvals`, reminder window) | Gating order, required approvals, reminder lookahead | Read-only |

The process CRM is authoritative for **process state**; the DMS/VDR/governance systems are
authoritative for the **facts they own** (NDA execution, access grants, approvals). The
tracker never overrides a system of record — it reflects and reconciles them.

## Citation format

`{system}:{ref}@{date}` — e.g. `crm:party=PB-1@2026-07-16`, `dms:nda=PB-2@2026-07-08`,
`vdr:access=PB-1@2026-07-09`, `gov:approval=AP-10@2026-06-30`, `crm:ms=MS-201@2026-06-30`.
Every party entry, bid, milestone reminder, and recorded approval in the output carries a
citation; uncited hard facts fail output validation.

## Freshness / effective dates

- Party, NDA, access, and approval state must be read **fresh**; a tracker is stamped with
  its `as_of_date` and reminders are computed against it.
- The change log diffs the current state against a **prior snapshot** whose `as_of_date` is
  recorded, so every logged change is reproducible and attributable.
- `stage_order`, `required_approvals`, and the reminder window are a **versioned config
  contract** (`config_version`), recorded on the output.

## Least-privilege operations (deployment)

- `crm.parties.read(process_id)`, `crm.milestones.read(process_id)` — read-only.
- `dms.nda.status(party_id)`, `vdr.access.status(party_id)` — read-only.
- `gov.approvals.read(process_id)` — read-only.
- `config.get('deal-process', version)`, `snapshot.get(process_id, as_of)` — read-only.

No mutation from this skill. It emits a **draft** tracker manifest (`tracker_status`
`draft-tracker`); any external delivery or system-of-record change is a separate,
human-approved action via the approval broker. The skill never sends outreach, executes an
NDA, grants VDR access, submits a bid, or writes an approval.
