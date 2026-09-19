# Changelog — investment-policy-statement-builder

## [0.2.1] — 2026-09-17

P4 live-model evaluation exposed invented priority ranks cited to sources that did
not supply them. Add a field-level source-to-input check, explicit null priority
and account-membership instructions, and preservation of missing-evidence
findings. Regression checks verify the existing script's null handling; no
calculation or schema behavior is changed. Initial failing model outputs remain
retained in the P4 evidence record; a fresh follow-up is reported separately.

## [0.2.0] — 2026-09-16

Independent review correction: require and preserve the upstream issue inventory with origin/status/citations; unresolved concerns remain findings, and external resolution requires cited dated evidence. Added executed carry-forward regressions. Also require approval party/role links to governance and consistent revision lineage; unknown parties and missing refresh lineage cannot produce review-ready.

Rebuilt for Wave 7 wealth management P1 with the shared `wealth-p0-v1` evidence envelope,
versioned/cited assumptions, full input-bound reconstruction, explicit unknowns and substantive
planning outputs. Preserves the distinct workflow job and draft-only human-review boundary.

Replaced section presence booleans with actual source-bound mandate content and readable draft. Preserves separate risk dimensions and human governing constraints; removes unsupported automatic most-conservative scoring. Pending approvals and account-scope checks are explicit. The 0.1 schema is intentionally replaced.

Executed domain/arithmetic regressions and contract tests accompany the package. SME/compliance review, source authentication, deployment connectors and real-agent acceptance remain separate release work. Historical notes below describe prior behavior and are not the current contract.

## Historical package notes

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). Created to assemble a
source-mapped **draft** Investment Policy Statement from documented inputs, separating drafting
from the downstream suitability review, proposal comparison, and trading (distinct entitlements,
evidence, and approvals).

- **Scope:** lay documented objectives, risk tolerance, time horizon, liquidity, tax, constraints,
  strategic allocation, rebalancing policy, benchmarks, and governance into the approved 13-section
  IPS template; map every material figure to a source; record advisor/compliance/client approvals as
  `pending`. Draft-only; no system-of-record change.
- **Controls:** R3; no suitability/Reg BI determination, no trading/staging, no finalization,
  filing, delivery, signature, or guarantees; overall risk tolerance governed to the most
  conservative dimension; allocation must sum to 100% and sit within bands; versioned template and
  tax-assumption contracts recorded on the draft.
- **Scripts:** `validate_input` (request schema, allocation-band and citation checks, needs-data
  warnings), `calculate_or_transform` (section assembly, risk reconciliation, allocation
  consistency, source map, completeness), `validate_output` (template fidelity, uncited/unsupported
  assertions, allocation tie-out, approval-pending, draft-only status flags, prohibited-language
  screen, standing note).
- **Evaluations:** trigger/routing tests, golden draft exercising all 13 sections and the
  consistency/citation checks, deterministic script checks, a non-compliant-draft safety fixture
  that fails closed (18 findings across every guardrail family), plus injection/guarantee/fabrication
  refusals and a finalize-and-send authorization refusal.
- **Handoffs:** upstream `financial-goal-progress-analyzer`, `retirement-income-scenario-modeler`,
  `client-review-preparer`; downstream `suitability-reg-bi-reviewer`, `portfolio-proposal-comparator`,
  `portfolio-rebalancing-assistant`, `advisor-follow-up-assistant`, `senior-investor-protection-screener`.

### Pending before release
- Wealth-management advisory + compliance/supervision blind review; legal review of standard
  disclosure language; accessibility review of the output template.
- Confirm the approved IPS template, required-section list, and approved tax-assumptions set —
  their owners, versions, and effective-date/stale-content controls.
- Wire read-only MCP integrations (CRM/planning, portfolio-accounting/OMS, product data,
  disclosures/restrictions register, approved tax assumptions) at deployment.
