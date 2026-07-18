# Adjacent-Skill Handoffs — procurement-sourcing-assistant

Sourcing-pack assembly (this skill) is a **separate control activity** from vendor-risk
determination, contract work, committee-pack assembly, and the award decision — each has
different entitlements, accountability, and downstream reliance. This skill emits a durable
`sourcing_id` and an assembled manifest; it does not perform the specialists', legal's, or the
committee's work.

## Downstream (this skill routes / hands off to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `third-party-risk-assessor` | A shortlisted/recommended supplier needs a third-party (operational/financial/concentration) risk assessment before award | `sourcing_id` + supplier ref + risk-input flag |
| `third-party-cyber-risk-reviewer` | A supplier will handle systems/data and needs an information-security / cyber review | `sourcing_id` + supplier ref + security risk flag |
| `third-party-ai-due-diligence-assistant` | The supplier provides an AI/model capability requiring model/data-governance due diligence | `sourcing_id` + supplier ref + AI risk flag |
| `contract-obligation-extractor` | A draft/executed agreement exists and its obligations/clauses need extraction | `sourcing_id` + supplier ref + agreement ref |
| `board-committee-pack-builder` | The award-recommendation goes to a governance committee/board forum | `sourcing_id` + assembled sourcing pack manifest |

## Upstream (feeds this skill)

| Upstream skill | Provides |
| -------------- | -------- |
| `enterprise-risk-assessment-builder` | Enterprise/category risk context that informs requirements and evaluation criteria |
| `enterprise-meeting-preparer` | Stakeholder intake / requirements-gathering meeting outputs to seed requirements |
| `meeting-action-tracker` | Tracked sourcing action items and owners feeding requirement owners and the timeline |

The procurement/sourcing system produces the raw sourcing event and bidder responses. This
skill is **interactive** assembly (`aws-fsi-scheduled-agent: no`); a monitor may populate a
queue but must not assemble, score, recommend, or decide.

## Non-catalog handoffs (human / licensed / operations)

- **Award / supplier selection / sourcing decision** → the sourcing lead, category owner, or
  procurement committee (no catalog skill makes a binding award). This skill only produces a
  cited, ranked draft recommendation.
- **RFP issuance / sending to bidders / bidder notification** → procurement operations, via the
  procurement system. Draft-only here.
- **Contract negotiation, redlining, signature, and PO issuance** → legal counsel and
  procurement operations (human, licensed).
- **External delivery** of the pack → a human approves and delivers via the approval broker;
  this skill never sends or submits.

## Duplicate-execution prevention

- This skill **does not** assess vendor risk, extract contract obligations, negotiate, or make
  the award — those belong to the named skills or to a human.
- The risk specialists and the committee-pack builder consume this skill's
  `sourcing_id`/manifest rather than re-assembling.
- A mandatory requirement that appears unmet is left as a `knockout-flag` for a human to
  confirm, never an autonomous elimination.
