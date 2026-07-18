# Changelog — service-recovery-assistant

## [0.1.0] — 2026-07-18
Initial authoring in the FSI Skills Library (baseline status: `new`). A Draft & package
skill that turns a customer service failure into an approval-ready remediation +
communication package, deliberately separated from formal complaint handling, vulnerability
support, and the execution of the outcome.

- **Scope:** score severity and customer impact, weigh precedent/policy/fair-value, compute
  a proposed remediation (documented direct redress + a matrix-bounded goodwill gesture),
  draft an apology in approved language with computed figures only, and record the required
  approval tier. Draft-only; never sends or pays.
- **Controls:** R2 / `external-delivery`; no send/deliver/pay/post; goodwill never above the
  matrix cap; redress only for a documented detriment (else `needs-data`); no
  liability/guarantee/entitlement/advice or "already actioned" language; versioned
  matrix/thresholds recorded via `matrix_version`.
- **Scripts:** `validate_input` (case schema, needs-data/referral warnings),
  `calculate_or_transform` (severity/impact scoring + goodwill matrix + redress + approval
  tier + drafted communication), `validate_output` (draft-only dispositions, required
  template sections, remediation tie-out + cap, computed-figures-only, recorded approvals,
  prohibited-claim/advice screen, standing note).
- **Assets:** `assets/output-template.md` service-recovery package template.
- **Evaluations:** trigger/routing, golden 6-case queue exercising every disposition and
  approval tier, deterministic script checks, a non-compliant package safety fixture
  (sent/liability/guarantee/advice/unsupported-figure → fail closed), prompt-injection and
  advice refusals, and a send/pay authorization refusal.
- **Handoffs:** upstream `customer-interaction-summarizer`, `knowledge-answer-composer`;
  referral to `complaint-resolution-assistant`, `vulnerable-customer-support-assistant`,
  `next-best-action-assistant`, `call-quality-compliance-reviewer`; post-approval delivery
  via `omnichannel-case-orchestrator`.

### Pending before release
- CX / complaints control-owner + legal review of the approved apology language and the
  fair-value / no-liability wording; conduct (fair-treatment) sign-off.
- Confirm the approved goodwill/redress matrix, cap, and approval thresholds source, owner,
  and versioning; align tiers with the deployment's delegated authority.
- Wire read-only MCP integrations (case/complaint mgmt, CRM, transcripts, knowledge/terms,
  approved-calculation) at deployment.
