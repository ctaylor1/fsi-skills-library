# Changelog — reserving-analysis-assistant

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). Prepares source-linked
reserving analyses from loss-development triangles as a controlled, review-ready draft —
separated from reserve selection, the Statement of Actuarial Opinion, individual claim
review, catastrophe modelling, and booking (distinct entitlements and authorities).

- **Scope:** volume-weighted / simple-average chain-ladder development factors, CDFs (with
  tail), indicated ultimate and IBNR by origin, severity/frequency, large-loss summary, and
  an indicative min-max uncertainty range, assembled into a reserve-analysis exhibit.
  Draft-only; no system-of-record change.
- **Controls:** R2; never selects/books a carried reserve, never issues/signs a Statement of
  Actuarial Opinion, never opines on adequacy, never files; every figure ties to the
  triangle and cites its source (ultimate = reported + IBNR); methods/tail/thresholds are a
  versioned contract (`dataset_version`); NPI/PII minimization at the aggregate level.
- **Scripts:** `validate_input` (triangle/dataset schema, needs-data and anomaly warnings),
  analysis engine (chain-ladder + severity/frequency + large-loss + uncertainty →
  `draft-analysis` / `anomaly-flagged` / `needs-data`), `validate_output` (template fidelity,
  required approvals recorded/no self-approval, approved method, completeness + source
  mapping, tie-outs, adequacy/opinion/booking/filing language screen, standing note).
- **Assets:** `assets/output-template.md` reserve-analysis exhibit template with the eight
  required sections, an actuarial review/approval block (all sign-offs pending), and the
  standing disclaimer.
- **Evaluations:** trigger/routing, golden 4-segment dataset exercising every status and the
  large-loss flag, deterministic script checks, a non-compliant-exhibit safety fixture that
  trips the R2 guardrail (missing sections, unapproved method, tie-out break, self-approval,
  adequacy/booking/filing language, missing disclaimer), and no-selection / no-booking /
  no-adequacy-opinion / no-signing refusals.
- **Handoffs:** upstream claims data mart + actuarial parameter set, `claims-file-reviewer`,
  `catastrophe-exposure-monitor`; adjacent `reinsurance-treaty-interpreter`,
  `valuation-reviewer`, `management-reporting-packager`, `month-end-close-orchestrator`;
  downstream the appointed actuary (selection, opinion) and finance (booking, filing).

### Pending before release
- Actuarial control-owner (appointed actuary) + model-risk review; confirm approved methods,
  tail factors, large-loss thresholds, and segmentation against the current actuarial
  parameter set and jurisdiction packs (US default; add packs per deployment).
- Confirm the reserve-analysis exhibit template owner, version, and effective dates.
- Wire read-only MCP integrations (claims/loss-triangle mart, policy administration,
  underwriting rules, actuarial/catastrophe data, document intelligence, producer systems);
  reserve selection, opinion, and booking remain human actions outside this skill.
