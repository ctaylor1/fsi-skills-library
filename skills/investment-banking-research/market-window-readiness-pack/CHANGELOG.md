# Changelog — market-window-readiness-pack

## [0.1.0] — 2026-07-19
Initial authoring in the FSI Skills Library (baseline status: `new`; 2026 industry-expansion
cohort).

- **Scope:** deterministic deal-launch readiness checks — attestation presence/evidence,
  justified-N/A handling, gate-item (due diligence, board approval) enforcement, and a by-category
  readiness score; each gap cited; review-only disposition.
- **Controls:** R2 draft-only; NEVER decides/approves launch, clears pricing, or gives
  market-timing advice; missing attestations never assumed satisfied; unjustified/gate-item N/A
  always gaps; MNPI/information-barrier controls; `external-delivery` approval.
- **Scripts:** `validate_input` (checklist + attestations), `calculate_or_transform` (match →
  flag → score), `validate_output` (citation coverage, review-only disposition, no-launch/timing
  screen, disclaimer).
- **Evaluations:** trigger/routing, golden readiness (gate/evidence/justified-N/A/score),
  gate-item-N/A edge, deterministic script checks, no-launch safety + injection, external-delivery
  authorization.
- **Handoffs:** `financing-alternatives-calculator`, `research-publication-preparation-assistant`,
  `capital-structure-maturity-mapper`.

### Pending before release
- IB/DCM/ECM/syndicate owner review; launch-checklist and gate-item config sign-off.
- Wire read-only deal-attestation/config MCP integrations at deployment.
