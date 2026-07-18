# Changelog — next-best-action-assistant

## [0.1.0] — 2026-07-18
Initial authoring in the FSI Skills Library (baseline status: `new`). Created to give service
agents and relationship managers a controlled, source-grounded way to draft next-best-actions
from customer context, while keeping binding decisions out of scope.

- **Scope:** rank policy-compliant service, education, referral, and retention actions from an
  approved action catalog and customer context; gate by eligibility, consent/do-not-contact,
  and vulnerability; exclude and route any binding credit, claim, or investment/suitability
  decision. Draft-only; no system-of-record change.
- **Controls:** R2; draft-only; `external-delivery` approval. The catalog is the allow-list;
  every recommendation is cited; no unsupported/guarantee/advice claims; no sending/submitting;
  outbound needs channel consent; retention/cross-sell suppressed for vulnerable customers.
- **Scripts:** `validate_input` (context + catalog schema, gap warnings), engine
  (`calculate_or_transform`: eligibility + consent + vulnerability gating, prohibited-decision
  routing, deterministic ranking, draft package assembly), `validate_output` (template
  fidelity, citation/support, prohibited-claim + draft-only scans, approvals recorded, standing
  note).
- **Assets:** `assets/output-template.md` (approved `nba-package-v1` package).
- **Evaluations:** trigger/routing (incl. suitability, complaint, vulnerable routing), golden
  7-action catalog exercising recommend / exclude(consent) / exclude(signal) / route(prohibited)
  / referral paths, deterministic script checks, a non-compliant-package safety check
  (`expect_exit 1`), no-binding-decision and prompt-injection refusals, external-delivery
  authorization refusal.
- **Handoffs:** upstream `customer-interaction-summarizer`, `omnichannel-case-orchestrator`,
  `knowledge-answer-composer`; boundary routing to `suitability-reg-bi-reviewer`,
  `loan-affordability-precheck`, `complaint-resolution-assistant`, `service-recovery-assistant`,
  `vulnerable-customer-support-assistant`, and licensed human specialists for actual decisions.

### Pending before release
- Customer-operations control-owner + marketing-consent/compliance blind review; fair-treatment
  and vulnerable-customer policy review; accessibility review of the package template.
- Confirm the approved action catalog + eligibility rules source, owner, and versioning; wire
  the consent, do-not-contact, and vulnerability flag reads to CRM at deployment.
- Confirm segregation of duties between drafting, approval/external delivery, and licensed
  decisioning.
