# Adjacent-Skill Handoffs — market-landscape-researcher

This skill produces a cited, reproducible **landscape brief** (`landscape_id`) covering the
eight dimensions and stops. It maps structure and evidence; it does not size the market to a
number, model a company, value anything, build the client deck, or make a call. Downstream
skills consume the `landscape_id` brief rather than re-researching the sector.

## Downstream (route the analyst to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `market-sizing-builder` | Convert the mapped demand-side and value-chain findings into TAM/SAM/SOM with methods and ranges | `landscape_id` + customers/economics dimensions + sources |
| `company-profile-builder` | Profile a specific named vendor surfaced in the competitive map | `landscape_id` + competitor name + share source |
| `comps-analysis-builder` | Turn the named peer set into a comparable-company analysis with multiples | `landscape_id` + ranked named firms |
| `coverage-initiation-researcher` | Extend the landscape into an initiating-coverage thesis for one name | `landscape_id` + strategic-implications dimension |
| `investment-banking-pitch-builder` | Assemble the (banker-reviewed) pitch book that includes a landscape section | approved `landscape_id` brief |
| `buyer-investor-list-builder` | Build a buyer/investor/sponsor universe informed by the transactions and competitor map | `landscape_id` + transactions dimension |
| `due-diligence-packager` | Fold the landscape into a data-room-backed diligence pack | `landscape_id` + sources |

Valuation and forecasting belong to the modeling skills (e.g., `dcf-modeler`,
`scenario-sensitivity-generator`) — this skill hands them context, never a valuation.

## Upstream (may call this skill)

`coverage-meeting-preparer` and pitch/coverage workflows may request a landscape brief as an
input section. No scheduled monitor is used here — this skill is interactive
(`aws-fsi-scheduled-agent: no`).

## Escalation to humans / licensed specialists

- Any request for a **buy/sell/hold call, rating, price target, or personalized investment
  view** → out of scope; route to a **licensed research/investment professional** under the
  firm's supervisory and disclosure process. Do not draft the recommendation.
- **MNPI / control-room / conflicts** questions (whether a name can be covered, wall-crossing)
  → route to the **control room / compliance** team before proceeding.
- **Legal or tax** interpretation of regulation surfaced in the brief → route to counsel; the
  brief describes the regulatory landscape, it does not opine.

## Duplicate-execution prevention

- This skill maps the landscape and evidences it; it must not size, model, value, or make a
  call — those belong to the downstream skills and to licensed humans.
- Downstream skills reuse the `landscape_id` brief and its citations rather than re-scraping the
  sector, keeping one source of truth for the landscape.
