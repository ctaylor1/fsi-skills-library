# Adjacent-Skill Handoffs — market-sizing-builder

This skill produces a transparent, source-linked **TAM/SAM/SOM sizing exhibit** (`sizing_id`)
with top-down and bottom-up methods, low/base/high scenarios, triangulation, and a cited
assumptions register, then stops. It does not value a security, forecast an integrated model,
issue a rating, or assemble a deck.

## Upstream (may call this skill)

| Upstream skill | Why it calls market-sizing | Handoff artifact |
| -------------- | -------------------------- | ---------------- |
| `market-landscape-researcher` | After qualitatively mapping an industry/theme, it needs the market quantified | market + segment definitions |
| `coverage-initiation-researcher` | An initiation draft needs a sourced market size for the industry section | market definition + `as_of` |
| `investment-banking-pitch-builder` | A pitch needs a market-opportunity exhibit built from approved drivers | market + drivers |

A scheduled agent is **not** used here (`aws-fsi-scheduled-agent: no`); the skill is interactive.

## Downstream (route the human/analyst to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `dcf-modeler` | The SOM/SAM should bound a revenue forecast inside a cash-flow valuation | `sizing_id` + reported SOM/SAM |
| `three-statement-model-builder` | The sizing feeds a revenue build in an integrated model | `sizing_id` + segment detail |
| `scenario-sensitivity-generator` | The analyst wants deeper sensitivity/breakeven around the softest drivers | `sizing_id` + assumptions register |
| `comps-analysis-builder` | Market growth/size supports a trading-comps narrative | `sizing_id` + summary |
| `investment-banking-pitch-builder` | The exhibit is assembled into a banker-reviewed pitch book | `sizing_id` + exhibit |
| A licensed **research / banking professional** (human) | The user asks whether to invest, wants a rating, price target, or valuation | `sizing_id` + drivers |

## Boundary with advice, ratings, and valuation

- This skill **models and reconciles market size**; it never recommends an action, never issues
  a rating or price target, never values a security, and never guarantees revenue or share.
  Those are advisory, rating, or valuation activities that require a licensed human and a
  supervised process — route to them with the `sizing_id`.

## Duplicate-execution prevention

- The skill computes both methods and the triangulation **once** and emits a durable
  `sizing_id`; downstream skills reuse that artifact rather than re-deriving the market size.
- It must not cross into valuation, forecasting, rating, or deck assembly — those belong to the
  human and the downstream skills.
