# Changelog — actuarial-model-run-assistant

## [0.1.0] — 2026-07-19
Initial authoring in the FSI Skills Library (baseline status: `new`; 2026 industry-expansion
cohort).

- **Scope:** deterministic volume-weighted chain-ladder over a cumulative loss triangle —
  age-to-age factors, cumulative development factors (with configured tail), and per-origin
  ultimate and IBNR from the latest diagonal, with a full assumption trail; indication for review.
- **Controls:** R2 model-and-calculate; NEVER books/sets a reserve, makes a reserving decision,
  or certifies adequacy; not-computable factors flagged rather than forced; `external-delivery`
  approval; NPI/PII handling.
- **Scripts:** `validate_input` (rectangular, contiguous-filled triangle + numeric tail),
  `calculate_or_transform` (chain-ladder), `validate_output` (ultimate=latest+ibnr and total
  tie-outs, no-reserving-decision screen, disclaimer).
- **Evaluations:** trigger/routing, golden chain-ladder math, not-computable-LDF edge,
  deterministic script checks, no-reserving-decision safety + injection, external-delivery authorization.
- **Handoffs:** `actuarial-data-lineage-checker`, `insurance-regulatory-filing-packager`.

### Pending before release
- Actuarial owner review; assumption-config mapping and method-selection governance sign-off.
- Wire read-only reserving-data + versioned-assumption-config MCP integrations at deployment.
