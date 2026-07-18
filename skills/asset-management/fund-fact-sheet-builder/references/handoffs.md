# Adjacent-Skill Handoffs — fund-fact-sheet-builder

Fact-sheet assembly (this skill) is a **separate control activity** from performance
calculation, exposure analysis, and commentary drafting — each has different inputs,
accountability, and downstream reliance. This skill emits a durable `factsheet_id` plus an
assembled manifest, a reconciliation ledger, and an open-items list; it does not perform the
performance analyst's calculation or the principal's approval and distribution.

## Upstream (feeds this skill)

| Upstream skill | Provides |
| -------------- | -------- |
| `performance-attribution-builder` | Verified standardized returns / attribution figures cited (not recomputed) as facts |
| `portfolio-exposure-analyzer` | Holdings, top positions, and allocation figures for the holdings section |
| `liquidity-stress-analyzer` | Liquidity/risk figures where the fact sheet reports a risk metric |
| `fund-commentary-drafter` | Approved narrative commentary, where the fact sheet includes a commentary block |

The performance, PMS/OMS, risk, and market-data systems produce the raw figures. This skill is
**interactive** fact-sheet assembly (`aws-fsi-scheduled-agent: no`); a monitor may populate a
queue but must not assemble, verify, approve, or distribute.

## Downstream / lateral (this skill hands off to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `investment-committee-memo-builder` | Fact-sheet figures index into an IC memo | `factsheet_id` + manifest + source index |
| `due-diligence-questionnaire-responder` | Fact-sheet figures answer a DDQ/RFP data point | `factsheet_id` + reconciliation ledger + citations |
| `mandate-compliance-monitor` | A holdings/exposure figure surfaces a possible guideline question | fund_id + figure + citation |

## Non-catalog handoffs (human / licensed / operations)

- **Performance verification** → performance measurement / GIPS control owner signs off that
  the standardized returns tie out. No catalog skill approves numbers for external use.
- **Compliance / marketing review and registered-principal approval** → the fund's compliance
  and a registered principal review the communication (retail-communication standards) and
  approve external use. No catalog skill — and not this skill — clears or approves the sheet.
- **External distribution / publication** → a human distributes via the approval broker; this
  skill never sends, submits, publishes, or shares.
- **MNPI / wall-crossing decisions** → the deal/portfolio team and compliance; MNPI/embargoed
  content is excluded from external fact sheets until they document clearance.
- **Investment advice, rating, or recommendation** → out of scope entirely; a fact sheet stays
  factual and non-promissory.

## Duplicate-execution prevention

- This skill **does not** calculate returns/attribution, analyze exposures, draft commentary, or
  monitor mandates — those belong to the named skills or a human.
- Downstream skills consume this skill's `factsheet_id`/manifest rather than re-assembling.
- A fund / share-class identity mismatch is left unresolved for a human, never auto-merged here.
- A figure that does not tie to source is an open item; it is not asserted and is not
  re-derived by this skill.
