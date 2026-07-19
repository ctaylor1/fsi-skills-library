# Changelog — underwriting-workbench-assistant

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). Created to give
underwriters a single, cited, decision-support workbench — compiling multi-source risk
information into an underwriter-ready profile and drafting decision rationale — while keeping
the regulated accept/quote/decline/bind decision entirely with a licensed human underwriter.

- **Scope:** compile a risk profile from entity, property, exposure, loss, catastrophe,
  financial, and third-party sources; assess completeness and source freshness; apply the
  approved underwriting rule set; surface findings/exceptions; and draft rationale. Draft-only;
  no system-of-record change.
- **Controls:** R3; no bind/quote/decline/issue, no autonomous underwriting decision, no
  policy-administration write; dispositions limited to `needs-data`, `refer-to-underwriter`,
  `ready-for-underwriter-review`; `human_adjudication` stays pending; unsupported-claim and
  binding/decision-language screens; versioned rules/appetite/authority config.
- **Scripts:** `validate_input` (submission-batch schema, needs-data warnings), the workbench
  compiler `calculate_or_transform` (completeness, freshness vs. SLA, approved rules,
  disposition, draft rationale), `validate_output` (allowed dispositions, evidence-backed
  findings, no unsupported claims, pending adjudication, template fidelity, binding-language
  screen, standing note).
- **Assets:** `assets/output-template.md` — the required underwriter-ready profile deliverable
  scaffold.
- **Evaluations:** trigger/routing, golden 4-submission batch exercising every disposition and
  route, deterministic script checks, no-autonomous-decision safety fixture (fails closed),
  prompt-injection and bind-refusal safety, and a decision-authorization refusal.
- **Handoffs:** upstream `submission-intake-triager`; adjacent `catastrophe-exposure-monitor`,
  `reinsurance-treaty-interpreter`, `coverage-gap-analyzer`, `policy-wording-comparator`,
  `policy-renewal-reviewer`, `reserving-analysis-assistant`; the underwriting decision is a
  human handoff.

### Pending before release
- Underwriting control-owner + chief-underwriting-officer review of the appetite/authority
  thresholds and referral routing; actuarial review of loss-ratio and catastrophe thresholds.
- Confirm the approved underwriting rules / appetite / authority config source, owner, and
  versioning; confirm per-line freshness SLAs.
- Wire read-only MCP integrations (policy administration, loss/claims, property/exposure,
  catastrophe model, financial, third-party risk) at deployment.
