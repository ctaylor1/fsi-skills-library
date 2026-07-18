# Changelog — earnings-results-analyzer

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** explainable post-earnings beat/miss analysis + cited evidence + a deterministic
  overall result classification + thesis-impact considerations. Read-only; no rating, no
  price target, no recommendation, no publication, no trade.
- **Classifications (deterministic):** per-metric surprise and Beat / In-line / Miss (with
  `lower_is_better` inversion); guidance Raised / Maintained / Lowered / Withdrawn / Initiated;
  factual transcript language changes vs. new disclosures — each explainable and evidenced
  (see `scripts/calculate_or_transform.py`).
- **Overall result mapping:** headline metrics drive Beat / In-line / Mixed / Miss /
  Undetermined, with a headline-guidance cut that prevents a clean beat on a guidance lowering
  (see `references/domain-rules.md`).
- **Controls:** R2; hard boundary against investment ratings, price targets, buy/sell/hold
  recommendations, personalized advice, coverage rating actions, publication, and trading;
  versioned-config tolerances only; MNPI / information-barrier discipline; `external-delivery`
  approval (supervisory-analyst / compliance for published research).
- **Scripts:** `validate_input` (metrics/guidance/transcript schema, evaluability warnings),
  classification engine, `validate_output` (evidence/citation completeness, deterministic
  overall-result tie-out, prohibited-decision language screen, disclaimer, thesis prompts).
- **Evaluations:** trigger/routing, golden Mixed case, no-headline and lower-is-better edges,
  deterministic script checks, no-recommendation safety + injection, external-delivery
  authorization.
- **Handoffs:** downstream to `three-statement-model-builder`, `dcf-modeler`,
  `comps-analysis-builder`, `scenario-sensitivity-generator`, `investment-committee-memo-builder`,
  `investment-thesis-monitor`, `coverage-meeting-preparer`; upstream from
  `coverage-meeting-preparer` / `coverage-initiation-researcher`. Rating/target/publication/
  trade are deliberately human, supervised steps with no catalog skill.

### Pending before release
- Domain SME (research/coverage) + control-owner (supervisory-analyst / compliance) blind review.
- Confirm the versioned tolerance / headline-set / mapping config source and its owner.
- Wire read-only MCP integrations (filings, transcript, estimates, prior model/note, config)
  at deployment.
