# Domain Rules — market-landscape-researcher

The repeatable procedure for mapping an industry, sector, or theme, and the deterministic
scorecards that make a landscape brief reproducible. Thresholds are configuration (versioned,
owned by the research/IB standards owner), not per-deal judgments, and never tuned to reach a
desired answer. Where a firm research standard or a jurisdiction pack applies, it takes
precedence over the defaults here.

## The eight required dimensions

Every landscape brief must address all eight, each with at least one **cited** finding:

| Dimension | Covers |
| --------- | ------ |
| `value_chain` | Stages from input to end consumption; who captures margin at each stage. |
| `competitors` | Named players, share/positioning, and the fragmented tail. |
| `customers` | Demand-side segments, buying behavior, switching costs, verticals. |
| `regulation` | Rules shaping the market (data, licensing, safety, disclosure, residency). |
| `technology` | Prevailing architecture and the fastest-moving capability frontiers. |
| `economics` | Cost structure, margins, unit economics, cyclicality, growth levers. |
| `transactions` | M&A and capital-markets activity (deals, take-privates, IPOs, rounds). |
| `strategic_implications` | Where value/differentiation is shifting; entrant and incumbent posture. |

A dimension with no cited finding is a **gap**; the output validator fails closed on any gap.

## Concentration metrics (deterministic; `scripts/calculate_or_transform.py`)

Computed over the **named** competitor set (the unattributed tail is reported separately, not
folded into a single synthetic firm):

- **CR4 / CR8** — sum of the top-4 / top-8 percentage shares.
- **HHI** — sum of squared percentage shares (0–10,000 scale).
- **Market-structure band** (factual descriptor, standard antitrust thresholds):

  | HHI | Band |
  | --- | ---- |
  | `< 1500` | unconcentrated |
  | `1500 – 2500` | moderately concentrated |
  | `> 2500` | highly concentrated |

These describe **market structure and evidence**, not attractiveness, and are explicitly not a
competition-law opinion or an investment view.

## Evidence-coverage & completeness scorecards

- `evidence_coverage`: cited findings vs. total, sources by tier, stale-source list, source date
  range. A load-bearing figure resting solely on a tier-4 source is a control flag.
- `dimension_completeness`: which of the eight dimensions carry a cited finding; any gap fails
  closed.

## Hard boundaries (fail closed)

- Never issue **investment advice, a recommendation, a rating, or a price target**, and never
  provide **personalized investment/legal/tax advice**.
- Never present a **valuation or trading conclusion** as a decision — hand context to the
  modeling skills instead.
- Never rest a **load-bearing figure** on an uncited or tier-4-only source.
- Never fold the unattributed tail into a fake "Other" firm to inflate or deflate concentration.
- Never tune the thresholds to reach a desired band or answer.

## Uncertainty prompts (always include in `limitations`)

Share estimates vs. reported figures, the unattributed tail, disagreement between sources
(state the range), stale or low-tier sources, private-vendor visibility gaps, and the `as_of`
caveat for fast-moving transaction/technology items.
