# Changelog — credit-terms-covenant-extractor

## [0.1.0] — 2026-07-20
Initial authoring in the FSI Skills Library (baseline status: `new`; Wave 5 — 2026 industry
expansion). Utility extractor for the Asset Management credit-analyst persona.

- **Scope:** deterministic extraction of seven canonical credit terms — maturity, coupon,
  seniority, collateral, call provisions, covenants, and baskets — from one controlled credit
  document, with a page-level citation on every field. Read-only; point-in-time; no monitoring.
- **Normalization (deterministic):** dates→ISO-8601, coupon→rate/type/frequency (fixed vs
  floating index+spread), seniority→ranked ladder, collateral→secured/priority, call features→
  factual booleans + first non-call date, covenant→incurrence/maintenance + captured threshold
  (never tested), basket→type + stated cap. See `scripts/calculate_or_transform.py`.
- **Controls:** R2; HARD BOUNDARY against covenant-compliance determination, covenant-test
  computation, interpretation of ambiguous/defined-term language, investment advice, and ongoing
  monitoring; ambiguity and conflicts routed to `needs_review`, never resolved; every term cited or
  not extracted; `external-delivery` approval.
- **Scripts:** `validate_input` (candidate schema; page-level citation required, fails closed),
  `calculate_or_transform` (normalizer with `--selftest` invariant check), `validate_output`
  (citation completeness, deterministic determination/advice screen, silent-ambiguity screen,
  disclaimer, durable `extraction_id`).
- **Evaluations:** trigger/routing, golden extraction vs bundled fixture, ambiguity/conflict edge,
  deterministic script checks, a fail-closed safety check running `validate_output` on a
  non-compliant fixture (determination language + silent ambiguity + missing citation → exit 1),
  injection, and external-delivery authorization.
- **Handoffs:** downstream to `covenant-compliance-monitor` (covenant testing),
  `credit-surveillance-packet` (ongoing monitoring), `credit-memo-drafter` (memo),
  `credit-risk-portfolio-analyzer` (portfolio analysis).

### Pending before release
- Domain SME (credit research) + control-owner blind review; sample-document extraction accuracy
  review against analyst-labeled golden terms.
- Confirm the versioned normalization rule-set source (field taxonomy, seniority ladder, ambiguity
  markers) and its owner in the controlled content library.
- Wire read-only MCP integrations (document-intelligence, entity resolution, content rules) at
  deployment.
