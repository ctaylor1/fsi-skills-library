# Changelog — investment-committee-memo-builder

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). A Draft & package
skill that assembles a decision-ready **draft** investment-committee memorandum from approved
private-markets inputs, separating memo drafting from model building, diligence, and the
committee decision (distinct owners, entitlements, and controls).

- **Scope:** assemble the nine required IC-memo sections (thesis, transaction structure,
  valuation, returns, base/upside/downside scenarios, risks & mitigants, position sizing &
  portfolio fit, recommendation & decision questions) from the model, diligence, market data,
  approved research, and portfolio context. Draft-only; no system-of-record change.
- **Controls:** R2 / `external-delivery`. Never makes or records the investment decision
  (`committee_decision` stays `pending`); never sends, circulates, or submits; never fabricates
  a figure or claim not traceable to an approved source; no personalized investment advice;
  mandatory downside case; single-name concentration breach blocks, sector breach is disclosed.
- **Assets:** `assets/output-template.md` — the controlled IC-memo template whose nine section
  keys are enforced by `validate_output`.
- **Scripts:** `validate_input` (build-request schema + needs-data warnings), the deterministic
  assembly engine (`calculate_or_transform`: model tie-outs, scenario consistency, sizing/limit
  checks, claim traceability, section assembly), and `validate_output` (independent gate:
  template fidelity, unsupported/unapproved-claim screen, tie-outs, recorded approvals,
  committee-decision-pending, prohibited-language screen, standing note).
- **Evaluations:** trigger/routing, a golden IC memo exercising every check, deterministic
  script checks, and a safety check running `validate_output` on a NON-COMPLIANT memo
  (fabricated/unapproved claim, tie-out break, missing downside, limit breach, recorded
  decision, guarantee language) that must fail closed; plus injection, advice-refusal, and
  no-decision authorization checks.
- **Handoffs:** upstream `lbo-model-builder`, `three-statement-model-builder`, `dcf-modeler`,
  `scenario-sensitivity-generator`, `due-diligence-packager`, `market-landscape-researcher`,
  `portfolio-exposure-analyzer`; downstream `investment-thesis-monitor`,
  `board-committee-pack-builder`, `valuation-reviewer`. Decision, legal terms, and MNPI /
  wall-crossing sign-off are human handoffs.

### Pending before release
- Blind SME review (IC chair / senior deal professional) + compliance review of MNPI /
  information-barrier handling and marketing-language controls.
- Confirm the firm's IC template + concentration-limit config source, owner, and versioning.
- Wire the read-only MCP integrations (model, VDR/diligence, market data, approved-research
  library, portfolio/limits, controlled template) at deployment.
