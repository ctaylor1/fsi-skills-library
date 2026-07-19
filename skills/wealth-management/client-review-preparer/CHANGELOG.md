# Changelog — client-review-preparer

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). Created to prepare an
audit-ready, fully source-cited wealth client-review pack (brief, agenda, deck outline) for
mandatory human adjudication — separating pre-meeting preparation from recommendation,
suitability review, trading, delivery, and post-meeting follow-up.

- **Scope:** resolve the household and accounts; assemble goals, holdings + portfolio summary
  (per-account and household tie-outs), performance, plan items, prior notes, service history,
  life events, open actions (overdue flags), a discussion agenda, and required disclosures from
  an approved template. Draft-only; no system-of-record change.
- **Controls:** R3; no investment recommendation, suitability decision, or trade; no closure,
  filing, or CRM/system-of-record write; no send/submit/deliver; no investment/legal/tax advice;
  nothing uncited; identity never guessed. Deterministic output screen fails closed on any miss.
- **Scripts:** `validate_input` (review-intake schema, status-driving warnings), assembler
  (identity + content-to-source integrity + freshness + holdings/household tie-out + disclosure
  coverage + overdue actions + surfaced routing + pack assembly), `validate_output` (template
  fidelity, unsupported-claim/identity/tie-out/disclosure checks, recorded approvals,
  recommendation/decision/closure/filing/delivery/advice screen, standing note).
- **Assets:** `output-template.md` (approved review-pack template with a reviewer sign-off and
  recorded-approvals block; validated for section presence and no unfilled placeholders).
- **Evaluations:** trigger/routing, golden 8-review queue exercising every status (draft-review,
  needs-data, unresolved-entity, account-identity-gap, unsupported-content, stale-source,
  tieout-break, disclosure-gap), deterministic script checks, a fail-closed safety fixture
  (overreach: recommendation/decision/filing/delivery + tie-out/disclosure breaches), prompt
  injection, advice refusal, and no-delivery / no-closure authorization refusals.
- **Handoffs:** surfaces routes to `suitability-reg-bi-reviewer`, `portfolio-rebalancing-assistant`,
  `senior-investor-protection-screener`, `financial-goal-progress-analyzer`,
  `retirement-income-scenario-modeler`, `investment-policy-statement-builder`,
  `portfolio-proposal-comparator`, and post-meeting `advisor-follow-up-assistant`; licensed
  advisor/principal adjudication and tax/legal specialists as human handoffs.

### Pending before release
- Wealth advisory + compliance (Reg BI / Form CRS) blind review; segregation-of-duty review.
- Confirm the required-disclosure config, freshness thresholds, and approved template source,
  owner, and versioning.
- Wire read-only MCP integrations (CRM, portfolio accounting/custody, performance, planning,
  disclosure library) at deployment.
