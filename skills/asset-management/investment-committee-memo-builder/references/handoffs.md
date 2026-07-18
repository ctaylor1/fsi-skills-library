# Adjacent-Skill Handoffs — investment-committee-memo-builder

This skill **assembles** the IC memo from inputs other skills and humans produce. It does not
build the models, run the diligence, or make the decision. All skill names below exist in
`catalog/skills-catalog.json`.

## Upstream (feeds this skill — produce the inputs the memo consumes)

| Upstream skill | Produces | Handoff artifact |
| -------------- | -------- | ---------------- |
| `lbo-model-builder` | LBO returns / leverage model (PE) | model outputs (entry/exit, MOIC/IRR, leverage) |
| `three-statement-model-builder` | Operating model | projections underpinning returns |
| `dcf-modeler` | DCF valuation | valuation cross-check |
| `scenario-sensitivity-generator` | Base/upside/downside + sensitivities | scenario table |
| `due-diligence-packager` | Diligence pack (QoE, legal, commercial) | thesis, risks, mitigants, terms |
| `market-landscape-researcher` | Sector/market context | valuation-vs-peers, thesis support |
| `portfolio-exposure-analyzer` | Fund exposures / limits | sizing and portfolio-fit inputs |

The memo **ties out** to these sources; it never re-derives or re-scopes them. If a required
model or diligence input is missing, this skill returns `needs-data` and routes to the
producing skill rather than inventing the figure.

## Downstream / adjacent (this skill routes to)

| Skill | When | Handoff artifact |
| ----- | ---- | ---------------- |
| `investment-thesis-monitor` | After the committee approves and the deal closes | approved thesis + covenants to monitor over the hold |
| `board-committee-pack-builder` | Rolling approved deals into a board / IC quarterly pack | the draft-ready memo |
| `valuation-reviewer` | An independent challenge of the entry valuation is needed | valuation basis + comps |

## Peer skill (do not duplicate)

- A **lending / credit-committee** memo for a loan decision is `credit-memo-drafter`
  (Banking), not this skill. This skill is for a private-markets **investment** committee.

## Human / licensed-specialist handoffs (no catalog skill)

- The **investment decision and committee vote** are made by the human investment committee
  / portfolio manager — never by this skill. It leaves `committee_decision: pending`.
- **Legal terms and SPA / credit-agreement drafting** go to counsel (human).
- **Wall-crossing, MNPI handling, and any suitability/regulatory sign-off** go to compliance
  (human) before circulation.

## Duplicate-execution prevention

- This skill does **not** build models, run diligence, monitor the thesis, or record the
  decision — those belong to the upstream/downstream skills and to humans.
- It emits a single draft-ready memo keyed by `deal_id`; downstream consumers reuse that memo
  rather than re-assembling it.
- If inputs are incomplete it stops at `needs-data` and names the producing skill, instead of
  filling the gap with an unsourced figure.
