# Changelog — household-financial-planning-assistant

## 0.3.0 — 2026-10-04

- Add portable source-field review and exact-recipient draft gates for P5.
- Preserve existing calculation modes; distinguish native validation from separately reviewed source fidelity and audience scope.

## [0.2.1] — 2026-09-17

P4 live-model evaluation exposed invented priority ranks cited to sources that did
not supply them. Add a field-level source-to-input check, explicit null priority
and account-membership instructions, and preservation of missing-evidence
findings. Regression checks verify the existing script's null handling; no
calculation or schema behavior is changed. Initial failing model outputs remain
retained in the P4 evidence record; a fresh follow-up is reported separately.

## [0.2.0] — 2026-09-16

Independent review correction: require and preserve the upstream issue inventory with origin/status/citations; unresolved concerns remain findings, and external resolution requires cited dated evidence. Added executed carry-forward regressions.

Rebuilt for Wave 7 wealth management P1 with the shared `wealth-p0-v1` evidence envelope,
versioned/cited assumptions, full input-bound reconstruction, explicit unknowns and substantive
planning outputs. Preserves the distinct workflow job and draft-only human-review boundary.

Renamed from `financial-goal-progress-analyzer`; retained goal-progress mode, added household cash flow, debts and shared goal funding, and corrected inflation throughout extension calculations. The 0.1 input/output schema is intentionally replaced; migrate inputs to named source-bound pools and the explicit assumption contract.

Executed domain/arithmetic regressions and contract tests accompany the package. SME/compliance review, source authentication, deployment connectors and real-agent acceptance remain separate release work. Historical notes below describe prior behavior and are not the current contract.

# Changelog — financial-goal-progress-analyzer

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** project each stated goal to its target date under approved, versioned
  assumptions; compute a funded ratio + status band (On track / At risk / Off track);
  quantify shortfall/surplus; derive illustrative planning levers. Read-only; no
  recommendation, suitability determination, advice, guarantee, trade, filing, or system
  write.
- **Projection (deterministic):** balance grown at the approved return plus a period-end
  contribution annuity, with inflation handling for `real`-terms goals; deterministic band
  mapping and lever arithmetic (see `scripts/calculate_or_transform.py` and
  `references/domain-rules.md`).
- **Controls:** R3; `required` human adjudication; hard boundary against recommendation /
  suitability / advice / guarantee / trade / filing / closure; approved versioned assumptions
  only; estimates-not-guarantees caveats.
- **Scripts:** `validate_input` (goals schema, evaluability warnings), goal-progress engine,
  `validate_output` (evidence/citation completeness, deterministic band tie-out, summary-count
  tie-out, lever presence, prohibited-decision language screen, disclaimer).
- **Evaluations:** trigger/routing, golden mixed-band case (At risk / Off track / On track +
  not-evaluable), not-evaluable edge, deterministic script checks, no-decision safety +
  injection, human-adjudication authorization.
- **Handoffs:** downstream to `suitability-reg-bi-reviewer`,
  `retirement-income-scenario-modeler`, `portfolio-rebalancing-assistant`,
  `portfolio-proposal-comparator`, `client-review-preparer`, `advisor-follow-up-assistant`,
  `senior-investor-protection-screener`.

### Pending before release
- Domain SME (planning/investment committee) + control-owner blind review; Reg BI / conduct
  review of the status-band framing.
- Confirm the approved, versioned assumptions source (returns, inflation, thresholds) and its
  owner.
- Wire read-only MCP integrations (CRM, portfolio accounting/OMS, planning engine, product
  data, approved assumptions) at deployment.
