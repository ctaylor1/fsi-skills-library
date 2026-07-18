# Adjacent-Skill Handoffs — company-profile-builder

Profile-building (this skill) is a **separate control activity** from analysis, valuation
modeling, and deck assembly — each has different inputs, accountability, and downstream
reliance. This skill emits a durable `profile_id` plus an assembled manifest and open-items
list; it does not perform the analyst's or banker's work.

## Downstream (this skill hands off to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `investment-banking-pitch-builder` | The profile is a page in a client-facing pitch book | `profile_id` + assembled manifest + source index |
| `coverage-meeting-preparer` | The profile feeds a client/prospect briefing | `profile_id` + business/ownership/management sections |
| `due-diligence-packager` | Profile facts index into a data-room diligence pack | `profile_id` + source index + open items |
| `buyer-investor-list-builder` | The profiled company anchors a buyer/investor universe | `profile_id` + ownership/transactions sections |
| `transaction-process-tracker` | The profile becomes a tracked deal artifact | `profile_id` + status/open items |

## Upstream (feeds this skill)

| Upstream skill | Provides |
| -------------- | -------- |
| `comps-analysis-builder` | Trading multiples / operating metrics to cite in trading data and KPIs |
| `dcf-modeler` | Source-linked valuation outputs referenced (not recomputed) as facts |
| `earnings-results-analyzer` | Reported results / KPI drivers as sourced facts |
| `market-landscape-researcher` | Industry/competitive context for the business overview |

The market/financial-data and filings systems produce the raw facts. This skill is
**interactive** profile-building (`aws-fsi-scheduled-agent: no`); a monitor may populate a
queue but must not assemble, approve, or distribute.

## Non-catalog handoffs (human / licensed / operations)

- **Investment advice, rating, recommendation, or price target** → a licensed research
  analyst under Research supervisory/control-room review. No catalog skill — and not this
  skill — issues a rating or recommendation; a company profile stays factual.
- **External distribution** of the profile → a human approves (supervisory analyst +
  compliance/control room) and distributes via the approval broker; this skill never sends,
  submits, or shares.
- **MNPI / wall-crossing decisions** → the deal team and compliance/control room; MNPI is
  excluded from external profiles until they document clearance.

## Duplicate-execution prevention

- This skill **does not** build comps, run valuation models, analyze earnings, or assemble
  the deck — those belong to the named skills or a human.
- Downstream skills consume this skill's `profile_id`/manifest rather than re-assembling.
- A company-identity mismatch is left `unresolved` for a human, never auto-merged here.
