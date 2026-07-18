# Changelog — management-reporting-packager

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). Created to assemble a
controlled, fully cited DRAFT management report package from approved finance inputs, keeping
packaging separate from the underlying analysis, from close certification, and from delivery.

- **Scope:** compute vs-budget and vs-prior KPI variances, attach cited driver commentary,
  summarize subledger-to-GL tie-outs, build source lineage, flag exceptions/data gaps, record
  preparer/reviewer approvals, and write executive takeaways against the approved template.
  Draft-only; `delivery_status` is always `draft`.
- **Controls:** R2, `external-delivery`. Never delivers/submits/distributes/posts the pack,
  never marks a figure final/board-approved or records the delivery approval, never emits an
  unsupported claim, an overridden reconciliation break, or forward-looking/advice language.
  `package_status` is `blocked` unless every KPI is cited, every reconciliation ties, and
  preparer + reviewer are recorded.
- **Scripts:** `validate_input` (package-input schema, needs-data/blocking warnings), assembly
  engine (`calculate_or_transform`: variances + support tagging + tie-out + approvals + status,
  with a `--selftest` invariant check), `validate_output` (eight required sections, draft-only
  control, citation/support screen, status consistency, required-approval screen, prohibited
  delivery/final-approval/advice language, standing note).
- **Assets:** `output-template.md` — the approved eight-section management report template
  enforced by `validate_output`.
- **Evaluations:** trigger/routing (positive + negative to `fpa-variance-analyzer`,
  `gl-reconciler`, `month-end-close-orchestrator`, `audit-evidence-packager`), a golden 4-KPI
  pack exercising variances/tie-outs/approvals, deterministic script checks, and safety checks
  (non-compliant pack fails closed, no-send refusal, block-the-gap refusal, no-advice refusal,
  delivery-approval authorization).
- **Handoffs:** upstream from `fpa-variance-analyzer`, `gl-reconciler`, `financials-normalizer`,
  `regulatory-reporting-data-validator`; adjacent to `month-end-close-orchestrator`,
  `audit-evidence-packager`, `financial-statement-audit-assistant`, `valuation-reviewer`.
  Delivery is a human/operations action (no distribution skill in catalog).

### Pending before release
- Controller/FP&A control-owner + disclosure-controls review; segregation-of-duty review.
- Confirm the approved report template, reporting config (tolerances, required approvals, KPI
  definitions), and their owner/versioning.
- Wire read-only MCP integrations (consolidation/ERP-GL, subledgers, FP&A, template library,
  approval broker) at deployment.
