# Changelog — order-allocation-validator

## [0.1.0] — 2026-07-19
Initial authoring in the FSI Skills Library (baseline status: `new`; 2026 industry-expansion
cohort).

- **Scope:** deterministically test a proposed allocation against approved policy (quantity
  tie-out, pro-rata target vs proposed within tolerance, eligibility, timestamp ordering,
  documented-deviation rule); emit a cited exception packet with a review-only disposition.
- **Controls:** R3; NEVER allocates/re-allocates/amends/books an order, overrides eligibility,
  or certifies compliance; versioned policy config; quantity breaks routed to
  `trade-break-resolver`; `required` human approval.
- **Scripts:** `validate_input` (schema, weights, evaluability), `calculate_or_transform`
  (deterministic policy checks), `validate_output` (quantity tie/break consistency, citation
  coverage, review-only disposition, no-allocation-decision screen, disclaimer).
- **Evaluations:** trigger/routing, golden exception case, quantity-break edge, deterministic
  script checks, no-allocation-decision safety + injection, external-delivery authorization.
- **Handoffs:** downstream `trade-break-resolver`, `best-execution-reviewer`.

### Pending before release
- Trading-compliance control-owner review; allocation-policy config source/version sign-off.
- Wire read-only OMS/EMS + entitlements + policy-config MCP integrations at deployment.
