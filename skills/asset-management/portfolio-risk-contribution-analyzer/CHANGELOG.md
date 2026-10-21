# Changelog

## 0.2.0 — 2026-09-20

- Adopt Phase 1 ownership and canonical naming; preserve alias metadata.
- Require source-bound native validation and document bounded support.
 — portfolio-risk-contribution-analyzer

## Unreleased — Phase 1 integrity repairs

- Added complete original-input binding and reconstruction checks; native output does not authenticate sources or accept unreviewed extra fields.
- Repaired bounded calculation/input contracts and documented unsupported cases in references/phase1-contract.md.
- Updated synthetic golden fixtures and native evaluation commands; added cross-package behavioral regressions.

## [0.1.0] — 2026-07-20
Initial authoring in the FSI Skills Library (baseline status: `new`; Wave 5 — 2026 industry
expansion).

- **Scope:** deterministic, source-linked risk-contribution packet — ex-ante portfolio risk
  and its Euler decomposition into marginal (MCR), total (TRC), and percentage (PCR)
  contributions per position and group; reconciliation to the approved risk engine total; and
  material changes since the prior review — as a draft for review.
- **Controls:** R2; never sets/changes a risk limit, never mandates or recommends a trade,
  rebalance, or hedge, never gives investment advice; assumptions carry provenance; methodology
  carries a version; MNPI handling; `external-delivery` approval.
- **Scripts:** `validate_input`, `calculate_or_transform` (deterministic risk decomposition,
  reconciliation, material-change comparison), `validate_output` (independent tie-out
  re-derivation, Euler/PCR/group checks, reconciliation consistency, methodology/version and
  provenance, limit-setting/mandate/advice screen, disclaimer). Each runs `--selftest` over a
  bundled fixture and prints a line ending "N error(s)".
- **Evaluations:** trigger positive/negative, routing (exposure vs contribution and adjacent
  skills), golden decomposition, deterministic script checks, a safety fixture that fails
  closed on broken tie-outs + a bad reconciliation + limit-setting/mandate/advice language +
  missing disclaimer, injection refusal, and external-delivery authorization.
- **Handoffs:** adjacent `portfolio-exposure-analyzer` (exposures vs risk contributions);
  downstream `investment-committee-memo-builder`, `investment-mandate-reviewer`,
  `market-risk-limit-monitor`, `fund-fact-sheet-builder`; limit-setting routed to the human
  risk committee.

### Pending before release
- Domain SME (portfolio risk / model governance) blind review; methodology and covariance
  source review.
- Wire read-only PMS/OMS, approved-risk-model, approved-risk-engine, and packet-store MCP
  integrations at deployment.
