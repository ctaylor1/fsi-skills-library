# Changelog — portfolio-holdings-summarizer

All notable changes to this skill package. Versions follow semver in `aws-fsi-version`.

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `existing-no-changes`
relative to the AWS baseline; authored fresh here).

- **Scope:** informational, read-only holdings summary with source-linked figures.
- **Triggers:** positive (summarize/what do I own/top positions/allocation); negative
  (advice, suitability, performance) with routing to adjacent skills.
- **Controls:** R1; no advice/recommendation (deterministic language screen), no
  price invention, no account/date merging; external-delivery human approval.
- **Tools/data:** read-only positions, reference/market data, document-intelligence;
  durable `snapshot_id`.
- **Scripts:** `validate_input.py` (schema, single account/date, citations, data-quality
  warnings) and `validate_output.py` (weight tie-outs, citation coverage, advice screen,
  disclaimer presence).
- **Evaluations:** trigger/routing, golden normal + multi-account edge, deterministic
  script checks, no-advice safety, prompt-injection, external-delivery authorization.
- **Handoffs:** downstream to `portfolio-risk-diversification-check`,
  `suitability-reg-bi-reviewer`, `performance-attribution-builder`, `client-review-preparer`,
  `portfolio-proposal-comparator`.

### Pending before release
- Domain SME + control-owner blind review; accessibility review of the output format.
- Wire read-only MCP integrations (positions, reference/market data) at deployment.
- With/without benchmark vs. no-skill baseline.
