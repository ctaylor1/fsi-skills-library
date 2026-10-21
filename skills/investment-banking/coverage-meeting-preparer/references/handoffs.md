# Adjacent-Skill Handoffs — coverage-meeting-preparer

Coverage-meeting preparation (this skill) is **prep-time drafting** — a separate activity from
profiling, analysis, valuation modeling, pitch assembly, diligence packaging, and delivery.
This skill emits a durable `engagement_id` plus a DRAFT brief with a citations index and a
recorded-approvals block; it does not perform the analyst's, banker's, or control room's work,
and it never delivers.

## Upstream (feeds this skill)

| Upstream skill | Provides |
| -------------- | -------- |
| `company-profile-builder` | Business/ownership/management facts as sourced context for the brief |
| `earnings-results-analyzer` | Reported results and KPI drivers as sourced developments |
| `market-landscape-researcher` | Sector/competitive context for the strategic issues |
| `comps-analysis-builder` | Trading multiples cited as context (never recomputed here) |

The CRM, filings, market-data, research, and data-room systems produce the raw facts. This
skill is **interactive** preparation (`aws-fsi-scheduled-agent: no`); a monitor may populate a
prep queue but must not assemble, approve, or deliver.

## Downstream (this skill hands off to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `investment-banking-pitch-builder` | The meeting warrants a client-facing pitch book | `engagement_id` + brief angle + source index |
| `due-diligence-packager` | The opportunity advances toward data-room diligence | `engagement_id` + open items + source index |
| `transaction-process-tracker` | A live opportunity becomes a tracked deal artifact | `engagement_id` + status/open items |
| `buyer-investor-list-builder` | A sell-side/buyer universe is needed off the discussion | `engagement_id` + relevant sections |

## Non-catalog handoffs (human / licensed / operations)

- **Investment advice, rating, recommendation, price target, or valuation opinion** → a licensed
  research analyst under Research supervisory/control-room review. No catalog skill — and not
  this skill — issues a rating, recommendation, or price; the coverage brief stays factual and
  frames objectives as hypotheses to test.
- **External delivery** of the brief → a human approves (supervisory banker + compliance/control
  room) and delivers via the approval broker; this skill never sends, files, posts, or shares.
- **MNPI / wall-crossing / control-room clearance** → the deal team and compliance/control room;
  MNPI is kept internal-only and is not externalized until clearance is recorded.
- **Live mandate, fee, or engagement-term decisions** → the banker with legal/compliance; the
  brief may restate a *sourced* status but never commits, prices, or negotiates.

## Duplicate-execution prevention

- This skill **does not** build the company profile, analyze earnings, research the sector,
  build comps, model valuation, assemble the pitch, or package diligence — those belong to the
  named skills or a human.
- Downstream skills consume this skill's `engagement_id`/brief rather than re-assembling it.
- A client-identity mismatch is left `unresolved` for a human, never auto-merged here.
