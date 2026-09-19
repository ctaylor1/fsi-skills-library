# 0.3.0 — 2026-09-18

Phase 3 native operations/incident/resilience capability added with source-bound outputs, explicit no-execution boundaries, negative-path regressions and evidence-gap retention. Offline acceptance only; specialist and deployment approvals remain open. Existing interfaces retained where present.

# Phase 1 — 2026-09-17

Corrected executable scope, evidence boundaries and/or naming; bundled canonical payment contract. Tests establish bounded offline behavior, not professional or deployment acceptance. See docs/payments/PHASE1-IMPLEMENTATION.md at repository level.

# Changelog — payment-service-incident-investigator

## [0.1.0] — 2026-07-19
Initial authoring in the FSI Skills Library (baseline status: `new`; 2026 industry-expansion
cohort).

- **Scope:** deterministic payment-gateway log diagnostics — PAN redaction, taxonomy
  classification, by-category/by-endpoint aggregation, top failing endpoint, most-frequent
  suspected cause, and per-category suggested (human-run) checks; redacted evidence pack.
- **Controls:** R2 read-only; NEVER changes config, rotates keys, disables rules, deploys fixes,
  or auto-remediates; **mandatory PAN redaction with an output leakage screen**; unknown codes go
  to `unclassified` (never guessed); `external-delivery` approval; PCI/NPI handling.
- **Scripts:** `validate_input` (entries + taxonomy), `calculate_or_transform` (redact →
  classify → aggregate → suggest), `validate_output` (PAN-leakage screen, no-remediation screen,
  category coverage, disclaimer).
- **Evaluations:** trigger/routing, golden diagnose (redaction + unclassified + top/suspected),
  all-unclassified edge, deterministic script checks, PAN+remediation safety + injection,
  external-delivery authorization.
- **Handoffs:** `payment-integration-readiness-pack`, `payment-fraud-rule-impact-analyzer`.

### Pending before release
- Payments ops/risk owner review; error-taxonomy and next-check mapping sign-off; PCI redaction
  scope confirmation with security.
- Wire read-only gateway/API-log + taxonomy-config MCP integrations at deployment.
