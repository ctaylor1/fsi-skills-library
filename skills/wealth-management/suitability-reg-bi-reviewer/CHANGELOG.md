# Changelog — suitability-reg-bi-reviewer

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** Reg BI (SEC 17 CFR 240.15l-1) and FINRA Rule 2111 suitability **evidence review** —
  obligation-by-obligation findings + cited evidence + a review-disposition band. Read-only; no
  determination, no approval, no trade, no closure, no filing.
- **Obligation checks (deterministic):** Disclosure (Form CRS, Reg BI disclosure, product
  disclosure), Care (profile completeness, reasonable-basis, cost considered, alternatives,
  rollover comparison, quantitative/series), Conflict of Interest (disclosed, proprietary/comp
  mitigated), Compliance (supervisory routing) — each explainable and evidenced (see
  `scripts/calculate_or_transform.py`).
- **Controls:** R3 decision-support; hard boundary against best-interest/suitability
  determination, approval/clearance/rejection, trade placement, case closure, and filing;
  versioned-config parameters only; `required` human adjudication by a supervisor/principal.
- **Scripts:** `validate_input` (packet schema, evaluability warnings), obligation-check engine,
  `validate_output` (evidence-traceability, deterministic disposition tie-out, prohibited-decision
  screen, disclaimer, open-item prompts). Each has `--selftest` over a bundled fixture.
- **Evaluations:** trigger/routing, golden Gaps-identified case, institutional (FINRA 2111) and
  Insufficient-evidence edges, deterministic script checks, no-decision safety + injection,
  required-adjudication authorization.
- **Handoffs:** to the human supervisor/principal and downstream to
  `senior-investor-protection-screener`, `conflicts-of-interest-reviewer`,
  `retirement-income-scenario-modeler`, `portfolio-proposal-comparator`,
  `investment-policy-statement-builder`, `regulatory-exam-response-packager`.

### Pending before release
- Domain SME (advisory/compliance) + control-owner blind review; legal/compliance review of the
  obligation-check set against current Reg BI / FINRA 2111 guidance and firm WSPs.
- Confirm the versioned check-parameter / disposition-mapping config source and its owner.
- Wire read-only MCP integrations (OMS, disclosures, CRM, product/planning, config) at deployment.
