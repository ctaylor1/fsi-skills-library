---
name: investment-risk-profile-reviewer
description: >-
  Capture and review a wealth client’s separately sourced investment-risk willingness, financial loss capacity, liquidity, horizon, experience and constraints. Use when an advisor or planner needs a review-ready risk-profile evidence record or to identify inconsistencies before an IPS, proposal or recommendation. Never invent questionnaire approval, choose a risk rating, collapse dimensions into a score or recommend an investment.
license: MIT
compatibility: Amazon Quick Desktop; local Python 3 standard-library validators and de-identified JSON fixtures; deployment requires read-only CRM, planning, evidence-library and controlled-policy MCP integrations. No live connectors are bundled.
metadata:
  aws-fsi-category: "Wealth Management"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 6 - wealth management P0"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US; deployment-controlled professional-capacity and policy profiles"
  aws-fsi-owner: "Wealth Management advisory & compliance"
  aws-fsi-primary-user: "Advisor / wealth planner / supervisor"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-09-16"
---

# Investment Risk Profile Reviewer

## Purpose and outcome
Give an advisor a complete, cited view of separate risk dimensions and unresolved conflicts.
The client's willingness to bear losses is distinct from financially assessed capacity, liquidity
needs, horizon, experience and constraints. The output preserves each source and leaves the risk
classification and investment decision to the authorized human.

## Use when
- Capture or refresh risk-profile evidence before an IPS, proposal or periodic review.
- Identify disagreement between stated willingness and assessed financial loss capacity.
- Compare an already supplied scenario or lockup against recorded risk dimensions.

## Do not use
- Select a portfolio, target allocation or risk rating → the advisor and approved assessment process.
- Legal best-interest evidence review → `investment-recommendation-evidence-reviewer`.
- Analyze investment holdings/exposure → `portfolio-exposure-analyzer`.
- Diagnose capacity or exploitation → `senior-investor-protection-screener` and qualified humans.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Pass the `artifact_id`, `input_hash`, source
registry and each dimension, including unresolved findings. A receiving skill may not turn an
unresolved conflict into an assumed moderate/aggressive score or an approval.

## Inputs and prerequisites
Use [references/schema.md](references/schema.md): common wealth-p0-v1 envelope, `profile_id`,
separate `dimensions`, and optional cited `proposed_exposure`. Willingness requires the actual
assessment/method/version/respondent plus a recorded method-approval reference; financial loss
capacity is a sourced professional assessment, not inferred from net worth by this script.

## Source hierarchy
Prioritize client-recorded responses, approved assessment-method records, source financial facts,
professional capacity analysis and documented product/scenario terms. See
[references/source-map.md](references/source-map.md). Source and approval metadata are evidence,
not authenticated authority. Never invent a missing response, method approval or financial analysis.

## Workflow
1. Confirm household, capacity, jurisdiction, review date and source validity.
2. Run `scripts/validate_input.py request.json`; reject malformed input and unsupported scope.
3. Run `scripts/calculate_or_transform.py request.json`. Preserve all six dimensions and any
   missing-source, missing-fact, willingness/capacity, liquidity, experience or horizon conflicts.
4. Review sources with the client/advisor as appropriate. Load
   [references/domain-rules.md](references/domain-rules.md) for calculation boundaries.
5. Run `scripts/validate_output.py pack.json` and hand the internal review draft to the authorized
   professional. Do not assign a rating or perform an investment/system action.

## Validation loop
The output validator reconstructs dimensions, arithmetic and findings from the structured source
snapshot. Any unrecorded rating, omitted dimension, altered metric, hidden finding or action claim
fails validation. Regenerate from corrected source-backed input; never suppress a conflict to pass.
Run `python -B scripts/test_domain.py` for executable regressions.

## Human approval
`required`. The advisor or appropriate qualified professional resolves contradictions, assesses
risk capacity and confirms the approved methodology. This package does not grant or authenticate
method approval, choose a rating or authorize a recommendation. See
[references/controls.md](references/controls.md).

## Failure handling
Missing dimension, source, method approval or material fact → needs-data with explicit findings.
Malformed numbers, duplicate identities, unsupported jurisdiction or invalid/stale registry → reject.
Different currencies → flag; do not invent FX. A source access failure stops the affected assessment.
A change to the household facts or method creates a new input hash and requires re-review.

## Output contract
The common envelope contains context/sources, `artifact_id`, `input_hash`, `status` and findings,
`human_review_required: true`, `action_taken: false`, `delivery_status: not-delivered`.
The result retains the structured `input_snapshot`, all six dimensions and known arithmetic:
capacity-loss percentage, willingness-loss amount and liquidity shortfall. Unknown metrics are null.
`assigned_risk_rating` is always null; `rating_decision` is not-made. Review-ready means only that
this evidence checklist is complete and no configured consistency issue was found.

## Privacy and records
Use pseudonymous household/respondent IDs, minimized descriptions and de-identified fixtures.
Source snapshots retain only facts needed to reproduce the review. Access, retention and delivery
follow controlled firm policy; no external connector or audit write is implemented.

## Gotchas
- Willingness is not financial ability, and a long horizon does not erase a near-term liquidity need.
- Capacity comes from a documented assessment; an arithmetic ratio is not a capacity model.
- No composite score, default risk category or silent choice between conflicting sources is permitted.
- Scenario loss and lockup are supplied evidence, not forecasts generated by this package.
