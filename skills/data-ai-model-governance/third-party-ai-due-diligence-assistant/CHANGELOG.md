# Changelog — third-party-ai-due-diligence-assistant

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). Packages third-party AI
due diligence for external providers, models, and data as a controlled, committee-ready draft —
separated from use-case intake, evaluation building, agent-scope review, and inventory
maintenance (distinct entitlements and systems of record).

- **Scope:** map submitted evidence to the required governance domains for the provider's
  criticality, check coverage and freshness against the versioned rubric, tie every finding to
  a bundled evidence item, compute a deterministic residual-risk rating, and draft a package
  with a recommended disposition from an approved template. Draft-only; no system-of-record change.
- **Controls:** R3; never approves/onboards/rejects a provider, never accepts risk, never signs
  or executes a contract, never updates an inventory, never asserts an unsupported finding;
  domains, thresholds, and hard gates are a versioned contract (`rubric_version`); every package
  carries `human_adjudication_required: true`; Confidential data minimization.
- **Scripts:** `validate_input` (engagement/evidence/findings schema, unclassified-criticality
  and unsupported-finding warnings), packaging engine (domain coverage + freshness + findings
  fidelity + residual-risk rubric with hard gates → status + recommended disposition),
  `validate_output` (known criticality, allowed status, human-adjudication flag, packageable
  invariants, unsupported-finding screen, approval/decision/risk-acceptance/contract-execution
  language screen, standing note).
- **Assets:** `assets/output-template.md` due-diligence package template with a reviewer
  adjudication block and standing disclaimer.
- **Evaluations:** trigger/routing, golden 7-engagement queue exercising every status and
  rating (proceed-with-conditions, remediate-before-onboarding, do-not-proceed via hard gate,
  insufficient-evidence, stale-evidence, unsupported-finding, needs-data), deterministic script
  checks, a non-compliant-package safety fixture that trips the R3 guardrail (unsupported
  finding, approval/decision + risk-acceptance language, missing human-adjudication flag and
  disclaimer), and no-decision / no-risk-acceptance / no-fabrication refusals.
- **Handoffs:** upstream `ai-use-case-intake-classifier` (tier/intake) and the rubric;
  adjacent `ai-evaluation-benchmark-builder`, `agent-permission-scope-reviewer`,
  `prompt-and-agent-risk-reviewer`; downstream (after human decision) `model-inventory-maintainer`.

### Pending before release
- AI / model-risk governance control-owner + third-party-risk committee review; segregation-of-
  duty review (assessor drafts, separate authority adjudicates).
- Confirm the due-diligence rubric source, owner, and versioning: required domains per
  criticality, accepted evidence types, freshness windows, risk-flag points, and hard gates,
  per jurisdiction pack.
- Confirm the controlled due-diligence package template owner, version, and effective dates.
- Wire read-only MCP integrations (rubric, model registry, data catalog, evaluation harness,
  agent/tool logs, risk/issue systems, templates) at deployment; the onboarding decision and
  inventory update remain human/routed actions outside this skill.
