# Changelog — loan-package-completeness-checker

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** completeness assessment of an underwriting/closing loan package against the
  versioned product + jurisdiction checklist — cited findings + a deterministic readiness
  recommendation. Read-only; R3 decision-support with mandatory human certification. No
  credit decision, no clear-to-close, no waiver, no certify/close/fund/book, no
  system-of-record write.
- **Checks (deterministic):** checklist coverage, required signatures, expiration to the
  certification `as_of`, cross-document consistency vs approved/expected terms (money =
  Blocker, identity = Exception), approval-envelope breaches, and outstanding/waived
  conditions — each explainable and evidenced (see `scripts/calculate_or_transform.py`).
- **Severity + readiness:** Blocker / Exception / Advisory map deterministically to
  Not-ready / Conditional / Complete (see `references/domain-rules.md`).
- **Controls:** R3; hard boundary against credit decisions, clear-to-close, adverse action,
  condition waivers, and certification/closing/funding; versioned-checklist config only;
  `required` human approval; PII minimization and masking.
- **Scripts:** `validate_input` (package schema, evaluability warnings), completeness engine,
  `validate_output` (evidence/citation completeness, counts + readiness tie-out,
  decision/closure/filing/waiver language screen, disclaimer, certifier-actions guard).
- **Evaluations:** trigger/routing, golden Not-ready case, missing-checklist edge, deterministic
  script checks, no-decision safety fixture (fails closed) + injection, human-certification
  authorization.
- **Handoffs:** upstream `credit-application-packager`, `loan-affordability-precheck`,
  `credit-memo-drafter`; downstream `fee-and-charge-reviewer`,
  `kyc-customer-due-diligence-screener`, `beneficial-ownership-verifier`,
  `covenant-compliance-monitor`, `loan-servicing-exception-resolver`.

### Pending before release
- Domain SME (credit/closing operations) + control-owner blind review; legal review of the
  per-jurisdiction checklist packs.
- Confirm the versioned checklist / validity-window / severity-mapping config source and owner.
- Wire read-only MCP integrations (origination/closing system, approval, checklist register,
  document intelligence, entity resolution) at deployment.
