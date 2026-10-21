---
name: private-fund-waterfall-reviewer
description: "Reconcile an explicitly supplied European whole-fund no-catchup distribution waterfall using unreturned LP capital, supplied accrued preference and a contractual residual split; surface unsupported variants without certifying carry or issuing distributions."
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
  aws-fsi-primary-user: "Private-fund accounting and carry reviewer"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-09-21"
---

# Contract-specific whole-fund distribution review

Reconcile an explicitly supplied European whole-fund no-catchup distribution waterfall using unreturned LP capital, supplied accrued preference and a contractual residual split; surface unsupported variants without certifying carry or issuing distributions.

## When to use

- Reconcile these approved LPA terms and supplied capital/preferred balances through the supported whole-fund tiers.
- Route elsewhere: Calculate an American deal-by-deal or catch-up waterfall, certify enforceable carry or release a payment.

## Work from the actual record

1. Establish object identity, review and knowledge dates, permitted audience, source versions, and accountable reviewer. Read [input/output schema](references/schema.md) and [bounded method](references/domain-rules.md). This is an unreleased development method; institutional acceptance is unestablished.
2. Prepare the native request from authorized original evidence. [Source map](references/source-map.md) distinguishes primary guidance from the operative contract and supplied assumptions. Preserve unknowns and open issues; never populate from an example merely to pass validation.
3. Run python3 -B scripts/validate_input.py INPUT.json and python3 -B scripts/calculate_or_transform.py INPUT.json. Local arithmetic does not fetch sources, confer permission or execute an investment action.
4. Run python3 -B scripts/validate_output.py OUTPUT.json --input INPUT.json against the retained original. This rejects modified results, extra narrative and embedded source records; hashing proves reproducibility, not truth.
5. Draft the [review artifact](assets/output-template.md) using only eligible cited outputs. Apply [controls](references/controls.md); preserve unresolved matters and follow [handoff boundaries](references/handoffs.md). Narrative review is separate from immutable native output.

## Supported method

Use an aggregate LP pool, without GP invested-capital participation. Tier1 pays min(cash, unreturned LP capital) to LPs. Tier2 pays min(remaining cash, supplied accrued preferred entitlement) to LPs. Tier3 pays carry_fraction of remaining cash to GP and the remainder to LPs. Sum tiers and verify distributable cash-LP total-GP total=0. Show capital/preference unpaid after the distribution. Preferred accrual is supplied, never inferred from elapsed time or a headline hurdle. Contract-specific state must already reflect prior distributions and be independently reviewed.

Do not change or approve a book, model, contract, commitment, vote, transfer or investment. A successful software check is not source authentication, legal applicability, expert acceptance or distribution permission.
