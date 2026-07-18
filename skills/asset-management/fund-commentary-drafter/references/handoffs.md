# Adjacent-Skill Handoffs — fund-commentary-drafter

Drafting commentary is an **artifact-assembly** activity. The numbers, exposures, and
compliance review it depends on are produced by other skills or by humans. This skill emits
a **draft package** (claim ledger + tie-outs + sign-off block); it must not reproduce the
analytics upstream or perform the compliance review downstream.

## Upstream (feeds this skill)

| Upstream skill | Provides | Handoff artifact |
| -------------- | -------- | ---------------- |
| `performance-attribution-builder` | Reconciled attribution by allocation/selection/currency with documented methodology and totals | `attribution` block (effects + total excess, cited) |
| `portfolio-exposure-analyzer` | Exposure/positioning by sector, factor, country, currency with lineage | `positioning` statements (cited) |
| `liquidity-stress-analyzer` | Liquidity/redemption context when the period narrative needs it | positioning/flows context (cited) |

Reconciled performance, flows, market data, the approved messaging library, disclosures, and
the template are supplied by the platform sources in
[source-map.md](source-map.md), not re-derived here.

## Downstream (this skill routes to)

| Downstream | When | Handoff artifact |
| ---------- | ---- | ---------------- |
| `communications-compliance-reviewer` | Required disclosure/prohibited-claim/supervision review of the drafted commentary before delivery | draft package + claim ledger + disclosures |
| Product / investor-relations reviewer (human) | Product sign-off on messaging and positioning consistency | draft package sign-off block |
| Compliance approver (human) | Compliance sign-off; then a human performs the actual external delivery | approved-for-delivery package |

The prohibited-claim and disclosure screen in `scripts/validate_output.py` is a
deterministic pre-check; it does **not** replace the human/compliance review performed by
`communications-compliance-reviewer` and the compliance approver.

## Not this skill (route elsewhere)

- A **fund fact sheet** (performance/holdings/risk/fees data card) → `fund-fact-sheet-builder`.
- An **investment-committee memorandum** (internal decision document) → `investment-committee-memo-builder`.
- **RFP / DDQ** answers from a content library → `due-diligence-questionnaire-responder`.
- A **board or committee pack** → `board-committee-pack-builder`.
- **Mandate/guideline breach** questions → `mandate-compliance-monitor`.

## Duplicate-execution prevention

- This skill **does not** compute attribution, exposures, or liquidity — it consumes their
  cited outputs.
- It **does not** approve or deliver — approvals are recorded by humans and delivery is a
  separate human action outside this skill.
- The claim ledger's citations let a reviewer trace each statement back to the upstream
  artifact rather than re-deriving it.
