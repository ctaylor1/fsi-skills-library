# Changelog — procurement-sourcing-assistant

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). Created to assemble
procurement **sourcing inputs** into one source-linked draft pack — separating sourcing-pack
**assembly and recommendation** from vendor-**risk determination**, **contract** work, and the
**award decision** (distinct controls, entitlements, and accountability).

- **Scope:** capture requirements, market scan, weighted evaluation criteria, and RFP content
  with citations; run a deterministic weighted scorecard over bidder responses; assign a bidder
  status (`scored` / `knockout-flag` / `needs-data`); rank fully-scored, mandatory-met bidders
  and mark the top as a DRAFT `recommended-pending-approval`; route vendor-risk items to the
  specialist skills; capture recorded and outstanding approvals; build a cited source index.
  Draft-only; no system-of-record change.
- **Controls:** R2; `external-delivery` approval; never awards a contract, selects a winning
  bidder, or makes a binding sourcing decision; never issues/sends/publishes an RFP or notifies
  bidders; never negotiates, commits spend, or issues a PO; never makes the third-party/cyber/AI
  vendor-risk or legal determination (routes them); never fabricates a requirement, score, or
  approval; no autonomous knockout (`knockout-flag` awaits human confirmation);
  `award_decision` stays `pending-human-approval`; versioned `required_sections` /
  `evaluation_criteria` weights / `required_approvals` / template.
- **Scripts:** `validate_input` (intake schema; unscored-criterion, missing-owner, weight-sum,
  and missing-evidence warnings), `calculate_or_transform` (deterministic scorecard + assembler
  → manifest), `validate_output` (required sections, no unsupported claims, weighted-score
  tie-out, approvals recorded, no award/issuance/negotiation language, draft status + pending
  award decision, standing note).
- **Assets:** `output-template.md` (sourcing-pack-template@0.1.0) — the human-facing pack render
  whose sections mirror the enforced manifest sections.
- **Evaluations:** trigger/routing, golden 3-bidder intake exercising every bidder status
  (scored / knockout / needs-data), the draft recommendation, approvals, and risk routing;
  deterministic script checks; and a safety fixture that fails closed on award/selection,
  RFP-issuance, and negotiation/commitment language, uncited claims, and a fabricated
  weighted score; injection, fabrication, and delivery-authorization refusals.
- **Handoffs:** downstream routing to `third-party-risk-assessor`,
  `third-party-cyber-risk-reviewer`, `third-party-ai-due-diligence-assistant`,
  `contract-obligation-extractor`, and `board-committee-pack-builder`; upstream from
  `enterprise-risk-assessment-builder`, `enterprise-meeting-preparer`, `meeting-action-tracker`.
  The award/supplier selection, RFP issuance, vendor-risk determinations, and contract execution
  are human-owned.

### Pending before release
- Enterprise Functions & Technology (procurement) control-owner review; segregation-of-duty
  review (pack assembly vs. vendor-risk determination vs. award decision).
- Confirm the per-category `required_sections`, `evaluation_criteria` weight standard, and
  `required_approvals` source, owner, and versioning (category playbook).
- Wire read-only MCP integrations (procurement/sourcing S2P, document intelligence, CRM/supplier
  master, contracts/CLM, knowledge base) at deployment.
