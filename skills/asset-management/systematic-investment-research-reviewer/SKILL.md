---
name: systematic-investment-research-reviewer
description: "Legacy supplied experiment review; explicit walk-forward label/feature chronology, embargo, historical universe and cost-path controls; no backtest or significance engine. Draft-only; use explicit extension and detached source validation."
license: MIT
compatibility: Python 3.10+ offline JSON; source connectors and professional approval systems are deployment prerequisites.
metadata:
  aws-fsi-category: "Asset Management"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 5 - 2026 industry expansion"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (MNPI / client-confidential)"
  aws-fsi-jurisdictions: "Contract and institution-specific; no legal determination"
  aws-fsi-owner: "Asset Management investment and operations"
  aws-fsi-primary-user: "Systematic investment researcher"
  aws-fsi-version: "0.2.0"
  aws-fsi-recertification-date: "2027-09-21"
---

# Systematic experiment control review

Review supplied systematic-investment experiments for temporal leakage, reused holdouts, trial selection risk and turnover-cost arithmetic; use before independent research review, without asserting strategy performance or authorizing deployment.

## When to use

- Review this dated experiment manifest before research committee review; show leakage and cost assumptions.
- Route elsewhere: Deploy the best strategy or certify that this backtest proves future alpha.

## Work from the actual record

1. Establish object identity, review and knowledge dates, permitted audience, source versions, and accountable reviewer. Read [input/output schema](references/schema.md) and [bounded method](references/domain-rules.md). This is an unreleased development method; institutional acceptance is unestablished.
2. Prepare the native request from authorized original evidence. [Source map](references/source-map.md) distinguishes primary guidance from the operative contract and supplied assumptions. Preserve unknowns and open issues; never populate from an example merely to pass validation.
3. Run python3 -B scripts/validate_input.py INPUT.json and python3 -B scripts/calculate_or_transform.py INPUT.json. Local arithmetic does not fetch sources, confer permission or execute an investment action.
4. Run python3 -B scripts/validate_output.py OUTPUT.json --input INPUT.json against the retained original. This rejects modified results, extra narrative and embedded source records; hashing proves reproducibility, not truth.
5. Draft the [review artifact](assets/output-template.md) using only eligible cited outputs. Apply [controls](references/controls.md); preserve unresolved matters and follow [handoff boundaries](references/handoffs.md). Narrative review is separate from immutable native output.

## Supported method

Check within-split date order; require train labels to end strictly before validation with the declared gap, and validation to end before test with the same gap. Future test completion, features available after use, holdout reuse and trials beyond the supplied limit remain explicit findings. Cost drag in basis points equals turnover fraction times one-way cost in basis points. It is a supplied-experiment cost diagnostic, not a computed or validated strategy return. No statistical significance, Sharpe ratio, portfolio simulation, multiple-testing probability or capacity estimate is invented.

Do not change or approve a book, model, contract, commitment, vote, transfer or investment. A successful software check is not source authentication, legal applicability, expert acceptance or distribution permission.

## Phase 4 specialist extension

Select `extension: walk-forward` explicitly for the bounded specialist method. Read [the Phase 4 contract](references/phase4-method.md), then use the existing input/calculation/output commands with a detached original input. The earlier schema remains available when `extension` is omitted. Unknown extensions fail. Use [the specialist review template](assets/phase4-template.md) and retain every residual, source gap and unsupported method. Source-linked calculations do not establish professional acceptance or execution authority.
