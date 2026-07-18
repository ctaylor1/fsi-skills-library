# Changelog — due-diligence-packager

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). Created to turn a raw
data room into an indexed, source-mapped diligence pack with cited extractions, an issue log,
open questions, completeness checks, and structured model handoffs — separated from the
modeling, valuation, profiling, and process-tracking skills that consume its output.

- **Scope:** index source documents, extract and cite key data, compile the issue log and
  open-questions list, check workstream completeness, and assemble validated model-handoff
  bundles. Draft-only; internal artifact.
- **Controls:** R2, Draft & package; action mode `Draft-only; no system-of-record change`;
  human approval `external-delivery`. Hard boundaries: never send/submit/deliver/file; no
  valuation opinion or investment recommendation; no unsupported claims (every data point
  cites an indexed source or is excluded as `needs-source`); model handoffs only to known
  modeling skills; completeness gaps always reported.
- **Assets:** `assets/output-template.md` (approved pack template; the required section
  anchors are enforced by `validate_output`).
- **Scripts:** `validate_input` (data-room manifest schema, unsupported-claim and
  missing-approval warnings, invalid-handoff errors), `calculate_or_transform` (packaging
  engine: source index, cited extractions, issue summary, completeness, validated model
  handoffs; excludes unsupported claims), `validate_output` (required sections, no
  unsupported claims, known model targets, recorded approvals + external-delivery gate,
  no send/submit or advice language, standing note).
- **Evaluations:** trigger/routing, golden data-room pack exercising every section and
  handoff, deterministic script self-tests, a non-compliant-pack safety check (`expect_exit
  1`), and no-delivery / no-advice / prompt-injection / external-delivery-authorization
  safety cases.
- **Handoffs:** downstream to `three-statement-model-builder`, `dcf-modeler`,
  `lbo-model-builder`, `merger-model-builder`, `comps-analysis-builder`,
  `scenario-sensitivity-generator`, `company-profile-builder`, and
  `transaction-process-tracker`; external delivery, legal opinions, and valuation/fairness
  opinions route to human/licensed owners (no catalog skill invented).

### Pending before release
- IB/Research control-owner and independent quality-reviewer blind review; MNPI /
  information-barrier control review; accessibility review of the pack template.
- Confirm the engagement's required diligence-workstream set, freshness window, and approval
  ledger source, owner, and versioning.
- Wire read-only MCP integrations (VDR/data room, document intelligence, filings,
  market/financial data, research corpus, CRM) at deployment.
