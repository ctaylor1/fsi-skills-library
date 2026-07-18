# Changelog — prospectus-plain-language-breakdown

All notable changes to this skill package. Versions follow semver in `aws-fsi-version`.

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `existing-updated` relative to
the AWS baseline; authored fresh here).

- **Scope:** informational, read-only plain-language breakdown of a prospectus / summary
  prospectus / KIID / offering document, with a page-level citation behind every statement.
- **Required coverage:** fees, strategy, liquidity, conflicts, risks, investor obligations —
  each covered or explicitly flagged as a disclosure gap.
- **Triggers:** positive (explain the prospectus / break down the fees / redemption terms /
  principal risks / conflicts); negative (advice/solicitation, wrong document type) with
  routing to adjacent skills.
- **Controls:** R2; no investment advice / recommendation / solicitation / suitability
  judgment / offer (deterministic language screen), no fabricated disclosures, no softening
  of risk language, no blending of share classes or documents; external-delivery human
  approval.
- **Tools/data:** read-only document-intelligence (page/section citation), approved-source
  retrieval (statutory prospectus / SAI incorporated by reference), entity resolution;
  durable `breakdown_id`.
- **Scripts:** `validate_input.py` (schema, page-anchor and page-range checks, required/
  recommended-topic coverage warnings) and `validate_output.py` (completeness, citation
  coverage, advice/solicitation screen, disclaimer presence).
- **References:** `source-map.md`, `controls.md`, `handoffs.md`, and `domain-rules.md`
  (required-topic set, fee taxonomy, liquidity terms, faithfulness rules).
- **Evaluations:** trigger/routing, golden normal + missing-topic and multi-class edges,
  deterministic script checks, no-advice + completeness safety, prompt-injection,
  external-delivery authorization.
- **Handoffs:** downstream to `suitability-reg-bi-reviewer`,
  `portfolio-risk-diversification-check`, `fee-and-charge-reviewer`,
  `fund-fact-sheet-builder` / `fund-commentary-drafter`,
  `senior-investor-protection-screener`; siblings `trade-confirmation-explainer` and
  `corporate-action-interpreter`.

### Pending before release
- Domain SME + control-owner blind review; accessibility review of the output format.
- Wire read-only MCP integrations (document-intelligence, approved-source retrieval,
  entity resolution) at deployment; add EU PRIIPs KID / UCITS KIID jurisdiction pack.
- With/without benchmark vs. no-skill baseline.
