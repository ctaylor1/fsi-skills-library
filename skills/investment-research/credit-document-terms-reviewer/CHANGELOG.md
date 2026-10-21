# Changelog — credit-document-terms-reviewer

## [0.3.0] — 2026-10-20

- Repair Phase 1 input/domain/source-vintage and faithful-partial controls; require whole-output reconstruction from separately retained originals.
- Preserve load-bearing identity, source/basis and review limits; source/role assertions remain unverified and cannot grant action authority.
- Update native schema, supplied-input documentation, positive fixtures and executable eval commands; add independent expected arithmetic, mutation and invalid-shape regressions.
- Bounded software evidence only; no new Phase 2 research engine, live action or institutional/practitioner acceptance.

## 0.2.0 — 2026-09-20

- Adopt Phase 1 ownership and canonical naming; preserve alias metadata.
- Require source-bound native validation and document bounded support.
 — credit-document-terms-reviewer

## 2026-09-20 — Phase 1 development corrections (unreleased)

- Repaired bounded native methods and disclosed their supported scope; see domain-rules and schema.
- Added detached original-input reconstruction, finite-JSON hashing and rejection of unvalidated output fields.
- Revised synthetic fixtures and independent operation regressions; no production, professional or institutional acceptance claimed.


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
  `issuer-credit-surveillance-reviewer` (ongoing monitoring), `credit-memo-drafter` (memo),
  `credit-risk-portfolio-analyzer` (portfolio analysis).

### Pending before release
- Domain SME (credit research) + control-owner blind review; sample-document extraction accuracy
  review against analyst-labeled golden terms.
- Confirm the versioned normalization rule-set source (field taxonomy, seniority ladder, ambiguity
  markers) and its owner in the controlled content library.
- Wire read-only MCP integrations (document-intelligence, entity resolution, content rules) at
  deployment.

## 0.3.0 — 2026-10-20

Added explicit Phase 2 supplied-evidence analytical mode while preserving the prior native contract and its regression evidence.
