# Changelog — submission-intake-triager

## [0.1.0] — 2026-07-18
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** ingest a commercial-insurance submission (broker email, ACORD, PDF, SOV, loss
  runs); normalize + reconcile exposure data across documents; detect gaps and draft broker
  follow-ups; triage against approved appetite rules; emit a cited intake packet with a
  routing recommendation. Read-only; no bind/quote/price/decline/issue, no closure.
- **Deterministic engine (`scripts/calculate_or_transform.py`):** field normalization,
  document-authority canonical selection, cross-document reconciliation (match / mismatch /
  single-source), gap detection + follow-up drafting, and five appetite rules
  (state, class, TIV capacity, loss ratio, catastrophe zone) each cited to evidence.
- **Routing bands (deterministic):** Out-of-appetite (recommend decline) → Incomplete →
  Refer → In-appetite; every band routes to a human underwriter.
- **Controls:** R3 decision support; hard boundary against any binding/pricing/closure
  action; versioned appetite config only; `required` human adjudication.
- **Scripts:** `validate_input` (submission/document/field schema, evaluability warnings),
  the engine, `validate_output` (band tie-out, evidence/citation completeness, mismatch
  surfacing, follow-up presence, prohibited-decision screen, disclaimer).
- **Evaluations:** trigger/routing, golden Refer case + Incomplete edge, deterministic script
  checks, no-decision safety fail-closed + injection, human-adjudication authorization.
- **Handoffs:** downstream to `underwriting-workbench-assistant`,
  `catastrophe-exposure-monitor`, `coverage-gap-analyzer`, `policy-wording-comparator`,
  `premium-quote-comparator`, `policy-renewal-reviewer`.

### Pending before release
- Domain SME (underwriting appetite/portfolio) + control-owner blind review; fairness review
  of the appetite rules and excluded-class list.
- Confirm the versioned appetite-config source, its owner, and per-line-of-business field
  packs (this baseline ships the commercial-property default).
- Wire read-only MCP integrations (document intelligence, policy admin, appetite config,
  third-party exposure) at deployment.
