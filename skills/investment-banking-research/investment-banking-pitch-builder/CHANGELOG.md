# Changelog - investment-banking-pitch-builder

## [0.1.0] - 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). Created to assemble a
banker-reviewed pitch-book **draft** from already-approved analyses, models, profiles, and
market pages against a versioned template - separating packaging/QA from the upstream
content construction and from control clearance and delivery.

- **Scope:** order pages by the template's required sections, attach a one-line takeaway and
  cited approved sources to every page, map each claim to an approved `source_ref`, check
  section completeness, record the required approvals, and set a delivery status.
  Draft-only; never sends, submits, distributes, or files.
- **Controls:** R2 / Draft-only / `external-delivery`. Fail closed on missing sections,
  unsupported or unapproved claims, promissory/guarantee/advice language, unrecorded
  approvals, or any delivered state. `approved-for-delivery` only when all required
  approvals (banker, control-room/compliance, legal/disclaimer) are recorded and approved.
- **Scripts:** `validate_input` (request schema; completeness/source/approval warnings),
  `calculate_or_transform` (assembly engine: ordering, per-page status, source mapping,
  approval roll-up, delivery status), `validate_output` (template fidelity, source mapping,
  no unsupported assertions, recorded approvals, draft-only screen, standing note).
- **Assets:** `assets/output-template.md` (required pitch-draft sections + approval block).
- **Evaluations:** trigger/routing, golden 6-page/6-section assembly, deterministic script
  checks, a non-compliant-draft safety fixture (`validate_output` exit 1), and refusal
  checks for send/fabricate/guarantee and unauthorized `approved-for-delivery`.
- **Handoffs:** upstream to the IB analysis/model skills (`comps-analysis-builder`,
  `dcf-modeler`, `three-statement-model-builder`, `merger-model-builder`, `lbo-model-builder`,
  `scenario-sensitivity-generator`, `company-profile-builder`, `market-landscape-researcher`,
  `market-sizing-builder`, `earnings-results-analyzer`, `buyer-investor-list-builder`,
  `coverage-meeting-preparer`, `due-diligence-packager`); adjacent control clearance via
  `conflicts-of-interest-reviewer` and `communications-compliance-reviewer`; MD/legal
  sign-off and delivery are human actions.

### Pending before release
- IB control-owner + legal/compliance blind review; segregation-of-duty review of the
  preparer vs. approver split.
- Confirm the approved template library source, owner, required-section set, and versioning.
- Wire read-only MCP integrations (template library, approved-artifact store, market data,
  filings, CRM, data room) at deployment; confirm no send/deliver capability is bound.
