# Changelog — privacy-impact-assessment-assistant

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). Created to assemble a
processing activity's privacy evidence into a controlled, source-mapped draft privacy /
data-protection impact assessment (PIA/DPIA) for human sign-off — distinct from data-lineage
mapping, third-party risk assessment, AI risk assessment, and the sign-off decision itself.

- **Scope:** marshal the eight PIA/DPIA evidence sections (processing purpose, personal-data
  inventory, legal basis & necessity/proportionality, data sharing & international transfers,
  retention, security, data-subject rights, mitigations) into the approved template, map every
  assertion to a source, flag gaps, compute a documented privacy-risk indicator, and attach a
  recommendation + approval ledger. Draft-only; no system-of-record change.
- **Controls:** R3; no approval/clearance of the processing, no lawful-basis-of-record change,
  no case closure, no DPIA filing or prior consultation, no system write, no send/submit. An
  unlawful-processing indicator (no lawful basis, special-category data with no Art 9 condition,
  restricted transfer with no mechanism) is a hard boundary (`blocked` + privacy-counsel route).
  Template-fidelity, no-unsupported-claim, required-approvals-recorded, and
  decision/filing/send language screens.
- **Scripts:** `validate_input` (intake schema, gap warnings → needs-information), packager
  (`calculate_or_transform`: section marshalling + deterministic privacy-risk + recommendation
  + approval ledger + specialist routes), `validate_output` (allowed draft status, all fourteen
  sections present, citations on present sections, approval ledger completeness, hard-boundary
  consistency, language screens, standing note). Stdlib-only, self-contained, `--selftest` on
  bundled fixtures.
- **Evaluations:** trigger/routing, golden DPIA case exercising every section and a High-band
  recommendation with a prior-consultation flag, deterministic script checks, and a fail-closed
  safety check running `validate_output` on a non-compliant assessment (decision/sign-off/
  filing/send language, unsupported claims, missing sections and approvals, hard-boundary
  mismatch) with `expect_exit 1`.
- **Handoffs:** upstream from `ai-use-case-intake-classifier`, `regulatory-change-impact-analyzer`,
  `policy-procedure-gap-analyzer`; specialist corroboration to `data-lineage-documenter`,
  `third-party-risk-assessor`, `ai-risk-assessment-builder`; downstream to human privacy sign-off
  (DPO / privacy officer / legal), which alone decides prior consultation with a supervisory authority.

### Pending before release
- Privacy/DPO control-owner + legal blind review; segregation-of-duty review (assessment
  drafting vs. sign-off vs. lawful-basis-of-record write).
- Confirm the approved output template + privacy-risk weighting source, owner, and versioning,
  and the jurisdiction pack (GDPR/UK-GDPR/CCPA-CPRA) per deployment.
- Wire read-only MCP integrations (DPIA register, RoPA/data inventory, data lineage, privacy
  program artifacts, regulatory corpus, information security / TPRM, records archive) at deployment.
