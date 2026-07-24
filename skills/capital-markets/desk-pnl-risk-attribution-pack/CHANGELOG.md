# Changelog — desk-pnl-risk-attribution-pack

## [0.1.0] — 2026-07-19
Initial authoring in the FSI Skills Library (baseline status: `new`; 2026 industry-expansion
cohort).

- **Scope:** deterministic desk-P&L attribution — explained = Σ risk components, unexplained
  residual vs tolerance with a break flag, and signed component contributions ranked by magnitude;
  each cited; review-only disposition.
- **Controls:** R3 draft-only; NEVER adjusts/restates/books P&L, signs off/attests/certifies, or
  approves a break; tolerance never invented; non-numeric components excluded and flagged;
  `external-delivery` approval; NPI/PII masking.
- **Scripts:** `validate_input` (reported P&L + numeric components + tolerance),
  `calculate_or_transform` (explained/residual/contributions), `validate_output` (explained+residual
  == reported identity, review-only disposition, no-adjust/sign-off screen, disclaimer).
- **Evaluations:** trigger/routing, golden attribution (explained/residual/break/ranking),
  within-tolerance edge, deterministic script checks, no-adjust safety (language + tie) + injection,
  external-delivery authorization.
- **Handoffs:** `trade-break-resolver`, `best-execution-reviewer`.

### Pending before release
- Product-control owner review; attribution taxonomy and tolerance-config sign-off.
- Wire read-only P&L + risk-attribution feed MCP integrations at deployment.
