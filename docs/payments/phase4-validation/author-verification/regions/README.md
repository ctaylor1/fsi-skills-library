# Phase 4 regional/corridor author validation

Final owned source checkpoint, 2026-09-18.

- Cross-border designer: 37 domain regression methods. Optional bank regional design:18. Optional corridor liquidity:24. Total79 new domain regression methods.
- 41 executable package checks passed across the three packages, including21 preserved core/collection checks and20 newly added commands.
- 12 calls passed using standalone copies (input, calculation, output against independent input and regression CLI per package). See standalone-results.json; final copied package regression stderr gives37/18/24.
- Structural validation:3 packages,0 errors,0 warnings. Scoped Ruff E9/F passed. These are not unrestricted lint or specialist acceptance.
- source-manifest.json retains file hashes at this checkpoint.

Independent review found a material intermediary amount mismatch could leave corridor comparison readiness true. The author reproduced the retained GBP1 intermediary against the required GBP798.4 gross transfer, added exact per-correspondent principal conservation and an inspectable difference, and added regression37. Updated schema bounds fee deduction stages and unsupported intermediate-currency/split contracts. The independent evaluator retained initial output and reran the unchanged normal/adversarial cases successfully under its after-corridor-fix folder. Two schema issues were also resolved: fee jurisdiction documented and Interac beneficiary_review paths made explicit.

Sources support public orientation only. Case reviewers are supplied declarations, not authenticated professional acceptance. No raw local network adapter, payment initiation, FX trade, sanctions screening, local legal determination or production connector is delivered.
