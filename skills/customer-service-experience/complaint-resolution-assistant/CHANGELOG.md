# Changelog — complaint-resolution-assistant

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). Created to accelerate
fair, consistent complaint handling by producing a review-ready **draft** resolution package
while keeping the decision, delivery, payment, and regulatory reporting with humans.

- **Scope:** classify + prioritize a complaint, reconstruct a cited chronology, map the
  applicable standards and root cause, compute a documented **proposed** remediation
  (refund + simple interest + distress-and-inconvenience band + capped goodwill), and
  assemble a DRAFT final-response letter from the approved template. Draft-only; no
  system-of-record change.
- **Controls:** R2 / `external-delivery`; never sends, pays, closes, files a regulatory
  return, admits legal liability, or makes the binding uphold/reject decision; redress only
  where a firm error is documented; goodwill capped; versioned redress/standards/root-cause
  config.
- **Scripts:** `validate_input` (intake schema, needs-data/needs-review warnings),
  `calculate_or_transform` (classification, chronology, standards/root-cause mapping,
  deterministic remediation, draft-letter assembly, `--selftest` tie-out check),
  `validate_output` (allowed dispositions/outcomes, required template sections + DRAFT
  marker, recorded approvals, remediation tie-out + goodwill cap, unsupported-claim screen,
  no send/submit/file/close language, standing note).
- **Assets:** `assets/output-template.md` — the approved final-response letter template with
  the six required sections and the recorded-approvals block.
- **Evaluations:** trigger/routing, a golden 6-complaint package exercising every disposition
  and outcome (uphold, partial-uphold, not-upheld, needs-review, needs-data, refer-specialist),
  deterministic script checks, a non-compliant-output safety check (fails closed),
  no-liability-admission and no-legal-advice refusals, and a no-decision authorization check.
- **Handoffs:** upstream `customer-interaction-summarizer`, `knowledge-answer-composer`;
  downstream/lateral `omnichannel-case-orchestrator` (execution, approval-gated),
  `vulnerable-customer-support-assistant`, `service-recovery-assistant`,
  `call-quality-compliance-reviewer`; human handoffs for the decision, regulatory reporting,
  and legal/ombudsman referral.

### Pending before release
- Complaints / conduct-risk control-owner + legal review of the redress methodology (interest
  rate, D&I bands, goodwill cap) and the escalation-rights wording per jurisdiction pack.
- Confirm the approved standards map and effective-dated product terms source, owner, and
  versioning.
- Wire read-only MCP integrations (complaint/case management, CRM, transcripts, approved
  knowledge/product terms) at deployment.
