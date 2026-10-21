---
name: institutional-investment-solutions-planner
description: "Legacy supplied institutional candidate comparison; explicit dated liability cashflow and discount-factor scenarios with real-asset commitments and liquidity controls; no actuarial certification. Draft-only; use explicit extension and detached source validation."
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
  aws-fsi-primary-user: "Institutional solutions and asset-owner strategist"
  aws-fsi-version: "0.2.0"
  aws-fsi-recertification-date: "2027-09-21"
---

# Institutional candidate-fit planning

Compare supplied institutional alternatives against explicit liability cash needs, illiquidity limits and governance authority; use for asset-owner or OCIO planning without ranking investments, selecting managers or granting delegated authority.

## When to use

- Compare these candidate institutional solutions against our supplied liabilities, liquidity limit and decision rights.
- Route elsewhere: Choose the best manager, promise a target return or grant OCIO discretion.

## Work from the actual record

1. Establish object identity, review and knowledge dates, permitted audience, source versions, and accountable reviewer. Read [input/output schema](references/schema.md) and [bounded method](references/domain-rules.md). This is an unreleased development method; institutional acceptance is unestablished.
2. Prepare the native request from authorized original evidence. [Source map](references/source-map.md) distinguishes primary guidance from the operative contract and supplied assumptions. Preserve unknowns and open issues; never populate from an example merely to pass validation.
3. Run python3 -B scripts/validate_input.py INPUT.json and python3 -B scripts/calculate_or_transform.py INPUT.json. Local arithmetic does not fetch sources, confer permission or execute an investment action.
4. Run python3 -B scripts/validate_output.py OUTPUT.json --input INPUT.json against the retained original. This rejects modified results, extra narrative and embedded source records; hashing proves reproducibility, not truth.
5. Draft the [review artifact](assets/output-template.md) using only eligible cited outputs. Apply [controls](references/controls.md); preserve unresolved matters and follow [handoff boundaries](references/handoffs.md). Narrative review is separate from immutable native output.

## Supported method

The original request without `extension` retains its existing candidate-fit schema and method. For dated liability present values, parallel-rate sensitivity and real-asset liquidity scenarios, use `extension: liability-real-assets` and read [extension schema and method](references/liability-real-assets.md). The contracts cannot be mixed; unknown extensions fail. The extension consumes reviewed discount-factor triplets and asset/liability cashflows; it does not generate actuarial projections, calibrate curves, appraise real assets or optimize an ALM portfolio.

Compare illiquid assets to assets times the explicit maximum fraction using exact multiplication; display illiquid fraction at 12 places. At each liability date compare cumulative eligible availability to cumulative liabilities; negative headroom is a gap. Aggregate availability cannot exceed candidate assets in this unfinanced subset. Flag candidate actions outside the institution permitted delegation list. Report every candidate without ranking, suitability certification, manager selection or implied authority.

Do not change or approve a book, model, contract, commitment, vote, transfer or investment. A successful software check is not source authentication, legal applicability, expert acceptance or distribution permission.
