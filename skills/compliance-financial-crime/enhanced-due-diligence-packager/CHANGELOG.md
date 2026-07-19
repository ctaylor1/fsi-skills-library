# Changelog — enhanced-due-diligence-packager

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). Created to assemble a
higher-risk customer's enhanced due diligence evidence into a controlled, source-mapped draft
package for human adjudication — distinct from screening, ownership verification, adverse-media
disposition, sanctions adjudication, and the adjudication decision itself.

- **Scope:** marshal the nine EDD evidence sections (SoF, SoW, ownership, geography, adverse
  media, PEP/sanctions, expected activity, monitoring, overview) into the approved template,
  map every assertion to a source, flag gaps, compute a documented residual-risk indicator,
  and attach a recommendation + approval ledger. Draft-only; no system-of-record change.
- **Controls:** R3; no onboarding/retention/exit decision, no rating-of-record change, no case
  closure, no SAR/CTR/STR drafting or filing, no system write, no send/submit. Sanctions
  true-match is a hard boundary (`blocked` + specialist route). Template-fidelity,
  no-unsupported-claim, required-approvals-recorded, and decision/filing/send language screens.
- **Scripts:** `validate_input` (intake schema, gap warnings → needs-evidence), packager
  (`calculate_or_transform`: section marshalling + deterministic residual-risk + recommendation
  + approval ledger), `validate_output` (allowed draft status, all fifteen sections present,
  citations on present sections, approval ledger completeness, hard-boundary consistency,
  language screens, standing note). Stdlib-only, self-contained, `--selftest` on bundled fixtures.
- **Evaluations:** trigger/routing, golden EDD case exercising every section and a High-band
  recommendation, deterministic script checks, and a fail-closed safety check running
  `validate_output` on a non-compliant package (decision/closure/filing/send language,
  unsupported claims, missing sections and approvals) with `expect_exit 1`.
- **Handoffs:** upstream from `kyc-customer-due-diligence-screener`, `customer-risk-rating-reviewer`,
  `aml-alert-triager`; specialist corroboration to `beneficial-ownership-verifier`,
  `adverse-media-investigator`, `sanctions-match-adjudicator`; downstream to human adjudication
  and (post-adjudication only) `suspicious-activity-report-drafter`.

### Pending before release
- FIU/compliance control-owner + legal (SAR-confidentiality/tipping-off) blind review;
  segregation-of-duty review (packaging vs. adjudication vs. rating-of-record write).
- Confirm the approved output template + residual-risk weighting source, owner, and versioning.
- Wire read-only MCP integrations (case management, KYC/AML, screening, transaction monitoring,
  regulatory corpus, records archive) at deployment.
