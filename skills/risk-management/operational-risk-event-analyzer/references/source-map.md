# Source Map — operational-risk-event-analyzer

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Loss-event / GRC** system (position of record) | The event, its classification, gross loss, recoveries, status | Read-only |
| 2 | **Finance / GL** | Indirect costs, booked recoveries, confirmed loss amounts | Read-only |
| 3 | **Incident / change / HR** systems | Contributing-cause evidence (incidents, change tickets, training records) | Read-only |
| 4 | **Third-party inventory** | Vendor identity and contract context when a third party is a cause | Read-only |
| 5 | **Reference data** | Basel event-type / business-line taxonomy normalization | Read-only |
| 6 | **ERM config** (versioned) | Materiality thresholds, escalation thresholds, cause→theme mappings | Read-only |

The loss-event/GRC record is authoritative for the event and its financials. If a narrative,
incident note, or manager assertion conflicts with the recorded loss/recovery figures, cite
both and flag the discrepancy for the adjudicator — never silently overwrite the record.

## Citation format

`{system}:{ref}` — e.g. `lossdb:ORE-2026-0142`, `inc:INC-88421`, `chg:CHG-20455`,
`ins:CLM-771`, `fin:GL-2026-07-JE-5590`. Every finding cites the specific evidence row(s)
behind it; the materiality finding cites the loss record plus each recovery source.

## Freshness / effective dates

- The ERM **config** (thresholds, cause→theme and theme→remediation maps) is a **versioned
  contract**; the output records the `config_version` used so an analysis is reproducible.
- The analysis is bound to the event `as_of` date; late-arriving recoveries or reclassification
  change the figures and require a re-run, not an in-place edit.

## Least-privilege operations (deployment)

- `lossdb.get(event_id)` → the event record + financials + status.
- `gl.costs(event_id)` → indirect costs / booked recoveries.
- `incidents.get(ref)` / `changes.get(ref)` / `hr.training(ref)` → causal evidence rows.
- `thirdparty.get(vendor_id)` → vendor context (only when a vendor is a cause).
- `refdata.taxonomy('basel-oprisk')` → event-type / business-line normalization.
- `config.get('oprisk', version)` → thresholds + mappings.
All read-only, deterministic, durable `analysis_id`, below the fixed timeout; page long causal
histories as resumable stages. No mutating operation is registered for this skill.
