# Changelog — trade-confirmation-explainer

All notable changes to this skill package. Versions follow semver in `aws-fsi-version`.

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `existing-no-changes`
relative to the AWS baseline; authored fresh here).

- **Scope:** informational, read-only plain-language explanation of one securities trade
  confirmation (Rule 10b-10 fields), with source-linked figures and a money tie-out.
- **Triggers:** positive (explain this confirm / what did I pay-receive / why net ≠ price×qty /
  agent vs. principal); negative (advice, "was this a good trade") with routing to adjacent skills.
- **Controls:** R1; no advice/recommendation and no judgment of price/charges (deterministic
  language screen), no figure invention, no merging of confirmations; external-delivery human
  approval (supervised communications).
- **Domain rules:** Rule 10b-10 disclosures; capacity (agent/principal); commission vs.
  markup/markdown; SEC Section 31 / FINRA TAF; accrued interest and yield on debt; canonical
  net-amount tie-out (`principal + accrued ± charges`); `price_factor` quoting conventions.
- **Tools/data:** read-only clearing/confirmation, OMS/EMS, reference/market data; durable
  `explanation_id`.
- **Scripts:** `validate_input.py` (schema, dates, side/capacity, citation, data-quality
  warnings), `calculate_or_transform.py` (principal derivation + net-amount tie-out, normalized
  explanation object), and `validate_output.py` (completeness, tie-outs, citation coverage,
  no-advice screen, disclaimer presence).
- **Evaluations:** trigger/routing, golden normal + multi-confirmation edge, deterministic
  script checks, no-advice safety, prompt-injection, external-delivery authorization.
- **Handoffs:** downstream to `trade-break-resolver`, `best-execution-reviewer`,
  `communications-compliance-reviewer`, `corporate-action-interpreter`,
  `prospectus-plain-language-breakdown`.

### Pending before release
- Domain SME + control-owner blind review; accessibility review of the output format.
- Wire read-only MCP integrations (clearing/confirmation, OMS/EMS, reference data) at deployment.
- With/without benchmark vs. no-skill baseline.
