# Changelog — insurance-fraud-referral-reviewer

## [0.2.0] — 2026-09-18
- Implemented Phase 1 domain correctness and explicit unknown-state handling described in current domain rules.
- Added the shared insurance evidence envelope and output hash/metadata validation; provenance remains supplied, not authenticated.
- Added executable boundary and independent output-mutation regressions, migrated native synthetic fixtures, and regenerated valid golden outputs.
- Clarified native handoff requirements, draft/review limits, actor capacity and revision identity. Production configuration/professional acceptance remains outstanding.


## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). Created to let a claims
adjuster / SIU intake assemble an audit-ready **draft** fraud referral without ever making a
fraud finding or an adverse customer decision — a Draft & package skill separated from SIU
investigation and claim adjudication (distinct entitlements and outcomes).

- **Scope:** evaluate ONLY the approved versioned `FR-*` fraud indicators, score them
  explainably, recommend a routing disposition, and draft an SIU referral package from a
  controlled template. Draft-only; routing to SIU is a *proposed* human handoff.
- **Controls:** R3; no fraud finding/determination, no claim denial/closure/rescission/void,
  no adverse customer decision, no acting on SIU's behalf, no send/submit; approved indicator
  catalogue only; prior-SIU flag overrides to refer-to-siu; anti-defamation / customer-facing
  screen; approvals recorded as pending; versioned indicator config.
- **Scripts:** `validate_input` (claim-candidate schema, date sanity, needs-data warnings),
  the indicator engine (approved `FR-*` scoring + band + referral package + template-faithful
  document), `validate_output` (allowed recommendations, approved+cited indicators, band
  tie-out, referral completeness + template fidelity, pending approvals, fraud-finding/
  adverse-decision/defamation screen, standing note).
- **Assets:** `assets/output-template.md` — the controlled SIU referral template whose section
  headers are the template-fidelity contract.
- **Evaluations:** trigger/routing, golden 5-claim set exercising every disposition and the
  prior-SIU override, deterministic script checks, a non-compliant fixture that must fail
  closed (fraud finding + denial + unapproved indicator + defamation), prompt-injection and
  defamation refusals, and an SIU-decision authorization refusal.
- **Handoffs:** downstream to human **SIU** (no catalog skill adjudicates fraud),
  `subrogation-opportunity-screener`, and `claim-file-quality-reviewer`; upstream from
  `claims-triage-assistant` and `claim-file-quality-reviewer`.

### Pending before release
- SIU / claims control-owner + legal (anti-defamation, privilege) blind review; segregation-
  of-duty review.
- Confirm the approved fraud-indicator configuration source, owner, weights, and versioning
  against the insurer's anti-fraud plan and applicable state SIU requirements.
- Wire read-only MCP integrations (claims/policy administration, reference data, document
  intelligence, producer/third-party history) at deployment.
