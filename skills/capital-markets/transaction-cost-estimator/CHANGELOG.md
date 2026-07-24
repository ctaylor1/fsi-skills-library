# Changelog — transaction-cost-estimator

## [0.1.0] — 2026-07-19
Initial authoring in the FSI Skills Library (baseline status: `new`; 2026 industry-expansion
cohort).

- **Scope:** deterministic implementation-shortfall TCA — half-spread, commission, square-root
  market impact (with uncertainty band), delay, realized, and opportunity cost in bps and
  currency, signed by side, from a versioned methodology.
- **Controls:** R2 draft-only; NEVER routes/executes/cancels/amends an order, selects/recommends
  a venue/broker/algo, or asserts best execution; guards division by absent ADV; `external-
  delivery` approval.
- **Scripts:** `validate_input` (schema, evaluability), `calculate_or_transform` (deterministic
  cost components + uncertainty band), `validate_output` (component tie-out, bps↔currency tie,
  methodology-version + uncertainty-range presence, no-execution/venue-advice screen, disclaimer).
- **Evaluations:** trigger/routing, golden TCA, missing-ADV edge, deterministic script checks,
  no-execution-advice safety + injection, external-delivery authorization.
- **Handoffs:** `best-execution-reviewer`, `order-allocation-validator`.

### Pending before release
- Execution-quality control-owner review; TCA-methodology config source/version sign-off.
- Wire read-only OMS/EMS + market-data + methodology-config MCP integrations at deployment.
