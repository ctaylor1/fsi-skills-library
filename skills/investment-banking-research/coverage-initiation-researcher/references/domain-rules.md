# Domain Rules — coverage-initiation-researcher

Deterministic rules for assembling and grading an initiating-coverage draft. Thresholds and
the required-section set are **configuration** (versioned, owned by the research supervisory
function), not ad-hoc judgments. The rules govern *draft completeness and internal
consistency* — they never produce an investment decision, rating, or price target.

## Required sections (initiating-coverage draft)

Eight sections must be present and evidenced:

`business_model`, `industry`, `competitive_position`, `forecast`, `catalysts`, `risks`,
`valuation`, `thesis`.

A section is **evidenced** when it has at least `min_claims_per_section` (default 1) claims
and **every** claim carries a non-empty citation. A present-but-uncited section counts as
*unevidenced* and blocks readiness.

## Forecast internal-consistency checks

| Check | Rule (default config) |
| ----- | --------------------- |
| Year axis | `years` strictly ascending, same length as `revenue` |
| Revenue | each value numeric and positive |
| Growth tie-out | if `revenue_growth` supplied, `|provided − recomputed|` ≤ `growth_tolerance` (0.005) |
| Margin bounds | each `ebit_margin` within `[margin_min, margin_max]` = `[0.0, 1.0]` |

Any failed check is a **blocking forecast error**. `revenue_growth` is recomputed from
`revenue` and returned so the reviewer sees the modeled trajectory.

## Valuation triangulation (DRAFT range only)

- Each method (`dcf`, `comps`, …) supplies a `value_per_share` and a citation.
- `draft_value_range` = `{low: min, high: max}` across method values.
- `blended_midpoint` = Σ(weightₖ · valueₖ), computed **only** when weights cover exactly the
  supplied methods and `|Σweights − 1| ≤ weights_tolerance` (0.01).
- The range and midpoint are an **analytical draft range**, explicitly **not** a price
  target and **not** an approved house value.

## Readiness mapping (deterministic, documented)

| Band | Rule |
| ---- | ---- |
| **Not ready** | any missing/unevidenced required section, OR any forecast error, OR valuation incomplete |
| **Analyst review** | content complete and consistent, but open `data_gaps` exist OR `evidence_coverage < 1.0` |
| **Ready for supervisory review** | all sections evidenced, no forecast errors, valuation complete, coverage 1.0, no open gaps |

Readiness is a **workflow-state suggestion** for the analyst and reviewer. "Ready for
supervisory review" still requires supervisory analyst + research committee approval before
publication or external delivery — it is not a green light to decide, rate, or deliver.

## Hard boundaries (fail closed)

- Never issue an approved **rating** or **price target**; the proposed rating stays
  `draft-unapproved`.
- Never give **personalized investment advice** or use **guarantee/certainty** language.
- Never admit **MNPI** into the draft; proceed to delivery only when `mnpi_attestation` is
  true and the information wall is respected.
- Never **fabricate** a section, forecast, or valuation input to clear a readiness gap —
  surface the gap instead.
