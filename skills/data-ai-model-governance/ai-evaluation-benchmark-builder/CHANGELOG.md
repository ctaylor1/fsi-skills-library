# Changelog — ai-evaluation-benchmark-builder

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). Created to separate
evaluation-benchmark *design* from evaluation execution, results analysis, and model release
(distinct entitlements, artifacts, and decisions).

- **Scope:** draft a source-linked evaluation benchmark spanning task, trigger, regression,
  safety, robustness, latency, and cost — each with a representative dataset, metric,
  acceptance threshold, and baseline — plus a risk-scaled coverage matrix. Draft-only; the
  benchmark is a proposal for model-risk governance.
- **Controls:** R3; no running/scoring, no go/no-go/release/certification, no self-approval,
  no invented thresholds/baselines; unsourced values are `proposed` (needs-calibration);
  `governance_approval` stays `pending`; versioned methodology/threshold catalog (`spec_version`).
- **Scripts:** `validate_input` (request schema, provenance/coverage warnings), benchmark
  builder (`calculate_or_transform`: provenance resolution + metric-direction check +
  per-dimension sample minimums + status assignment + coverage matrix), `validate_output`
  (template fidelity, approved-only for ready evals, coverage integrity, required approvals,
  determination/certification language screen, standing note).
- **Assets:** `assets/output-template.md` (the drafted benchmark package for governance review).
- **Evaluations:** trigger/routing, golden 11-evaluation request exercising every status,
  deterministic script checks, a non-compliant-benchmark safety fixture (unknown dimension,
  unsourced-approved threshold, self-approval, certification language, missing standing note),
  no-run / no-invented-threshold refusals, and a self-approval authorization refusal.
- **Handoffs:** upstream `ai-use-case-intake-classifier`, `model-inventory-maintainer`;
  downstream an authorized evaluation harness (engineering/MLOps, human-operated — no catalog
  skill), `model-validation-assistant`, `model-risk-documenter`; specialists
  `prompt-and-agent-risk-reviewer`, `ai-risk-assessment-builder`.

### Pending before release
- AI/Model Risk Governance control-owner review of the threshold-provenance and coverage rules.
- Confirm the approved evaluation methodology + threshold catalog source, owner, and versioning
  (`spec_version`), and the per-dimension sample minimums and required-coverage-by-risk table.
- Wire read-only MCP integrations (model registry, data catalog, policy/risk-appetite library,
  evaluation harness metrics, agent/tool logs) at deployment.
