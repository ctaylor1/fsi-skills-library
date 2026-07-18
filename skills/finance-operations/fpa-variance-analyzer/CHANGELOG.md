# Changelog — fpa-variance-analyzer

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** explainable actual-to-budget / forecast / prior-period variances by driver +
  cited evidence + run-rate estimates + draft management commentary. Read-only; no management
  decision, no forecast commitment, no restatement, no posting.
- **Method (deterministic):** three-way variance per line; favorable/unfavorable from account
  type (not raw sign); versioned materiality screen (absolute + percent with a `min_base`
  floor); driver-decomposition tie-out (`ok`/`fail`/`unattributed`); run-rate impact for
  recurring lines labeled an estimate (see `scripts/calculate_or_transform.py`).
- **Controls:** R2; hard boundary against management decisions, forecast/guidance commitment,
  restatement, and journal posting; versioned-config thresholds only; no fabricated drivers;
  alternative-explanation caveats required; `external-delivery` approval.
- **Scripts:** `validate_input` (variance schema, evaluability warnings), variance engine,
  `validate_output` (evidence/citation completeness, independent driver tie-out, run-rate
  estimate labeling, deterministic priority tie-out, decision-language screen, disclaimer,
  caveats).
- **Evaluations:** trigger/routing, golden Elevated case (4 material findings across the
  absolute and percent paths, tie-out `ok`/`fail`/`unattributed`), thin-attribution edge,
  deterministic script checks, no-decision safety + injection, external-delivery authorization.
- **Handoffs:** downstream to `management-reporting-packager`, `gl-reconciler`,
  `financial-statement-audit-assistant`, `audit-evidence-packager`, `valuation-reviewer`,
  `regulatory-reporting-data-validator`; upstream from `financials-normalizer` and
  `month-end-close-orchestrator`.

### Pending before release
- Domain SME (FP&A/controllership) + control-owner blind review; fairness/conduct review of
  commentary language.
- Confirm the versioned materiality/attribution config source and its owner.
- Wire read-only MCP integrations (GL/consolidation, subledgers, FP&A/planning, config) at
  deployment.
