# Changelog — vulnerable-customer-support-assistant

## [0.1.0] — 2026-07-18
Initial authoring in the FSI Skills Library (baseline status: `new`). A Draft & package (R2)
copilot that turns the customer's own words in a service interaction into a cited, review-ready
support-needs assessment — never a diagnosis, a capacity determination, or a system-of-record
change.

- **Scope:** map cited signals to vulnerability drivers (Health, Life events, Resilience,
  Capability), suggest approved-catalog accommodations traced to each signal, and suggest an
  approved referral route (safeguarding-first priority). Draft-only; nothing recorded or sent.
- **Controls:** R2; no diagnosis, no mental-capacity/fitness determination, no discriminatory
  service limitation, no financial/medical/legal advice, no unapproved/unsupported suggestion,
  no autonomous CRM change or customer contact; heightened-risk signals force a safeguarding
  referral and a time-sensitive human-review flag; special-category data gated on captured
  consent; versioned drivers taxonomy + accommodations catalog + referral routes.
- **Scripts:** `validate_input` (interaction schema; source_ref / consent / masking warnings),
  `calculate_or_transform` (signal → driver map, approved accommodation selection, referral
  priority, template render, internal invariants), `validate_output` (approved & supported
  accommodations only, approved routes, required template sections, diagnostic/discriminatory/
  advice screens over generated text with customer quotes excluded, proposed-not-applied record
  gate, human-review gate, standing note).
- **Evaluations:** trigger/routing, golden 3-signal interaction exercising every disposition,
  deterministic script checks, a non-compliant fixture that must fail closed (unapproved &
  unsupported accommodation, diagnostic/discriminatory/advice language, applied record, missing
  sections, missing standing note), plus injection, no-diagnosis, and external-delivery
  authorization refusals.
- **Handoffs:** upstream `customer-interaction-summarizer`, `omnichannel-case-orchestrator`,
  `complaint-resolution-assistant`; downstream `next-best-action-assistant`,
  `service-recovery-assistant`, `call-quality-compliance-reviewer`; specialist/safeguarding and
  financial-difficulty referrals are human/operations actions, not skills.

### Pending before release
- Customer-service control-owner + data-protection (special-category consent) blind review;
  fairness/conduct review of the framing and prohibited-language screens.
- Confirm the approved drivers taxonomy, accommodations catalog, and referral routes source,
  owner, and versioning; wire the jurisdiction pack for each deployment.
- Wire read-only MCP integrations (CRM, transcripts, case management, complaint system,
  approved knowledge, product terms) at deployment.
