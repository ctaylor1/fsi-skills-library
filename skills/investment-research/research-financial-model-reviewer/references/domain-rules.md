# Method and supported scope

Independently recompute supplied formula graphs, reconciliations, assumption evidence and economic funding bounds; retain exact legacy roll-forward behavior without approving the model.

The domain helper validates structural, finite-number, basis and method conditions before computation; the separately retained original is required for complete output reconstruction. Supplied economic bounds and source metadata are evidence inputs, not institutional endorsements. Negative equity and failed funding checks remain visible. Professional acceptance remains not established.

Independent-review mode accepts input/formula cells, arithmetic + - * /, explicit reconciliation equations, assumption bounds and economic checks. Cycles, unknown names, executable syntax and nonfinite results fail. Formula checks recompute dependencies rather than trusting supplied formula cell values. Bounds are caller supplied; passing them establishes no universal economic truth. Legacy mode is exactly {"mode":"legacy-roll-forward","input": ORIGINAL_AUDITOR_INPUT}; legacy_result preserves the old native result, rounded residual, tolerance, IDs and explicit null structural breaks. The legacy implementation and validator are bundled locally and require detached originals.
