# Changelog — corporate-action-interpreter

All notable changes to this skill package. Versions follow semver in `aws-fsi-version`.

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `existing-updated` relative
to the AWS baseline; authored fresh here).

- **Scope:** informational, read-only interpretation of one corporate-action notice —
  event type, status, key dates, elective options, and deterministic cash/share
  entitlements on an eligible position, with ambiguities flagged for operations review.
- **Triggers:** positive (explain this event / what are my options and deadline / how much
  cash or how many shares); negative (advice on which option, submitting an election) with
  routing to adjacent skills.
- **Controls:** R2; no advice, no personalized tax advice, no election/instruction
  (deterministic prohibited-language screen), no term invention, no event/security merging;
  external-delivery human approval.
- **Tools/data:** read-only depository/agent notices, reference/market data, custody
  position, document-intelligence; durable `interpretation_id`.
- **Scripts:** `validate_input.py` (schema, date ordering, options/deadline/default,
  data-quality warnings incl. fractional exposure); `calculate_or_transform.py`
  (deterministic per-option cash/share entitlements with whole/fractional split);
  `validate_output.py` (entitlement tie-outs, citation coverage, no-advice/no-tax/no-binding
  screen, disclaimer presence).
- **Evaluations:** trigger/routing, golden normal + multi-event edge, deterministic script
  checks (input, transform, output), no-advice safety, prompt-injection, external-delivery
  authorization.
- **Handoffs:** upstream `portfolio-holdings-summarizer` (eligible position); downstream
  `corporate-action-election-assistant` (elect), plus non-skill owners — a licensed tax
  professional (tax basis), the corporate-actions operations team (post-event
  reconciliation), and the corporate-actions operations exception queue (ambiguities).

### Pending before release
- Domain SME + control-owner blind review; accessibility review of the output format.
- Wire read-only MCP integrations (notices, reference/market data, custody) at deployment.
- With/without benchmark vs. no-skill baseline.
