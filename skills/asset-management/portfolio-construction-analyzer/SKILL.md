---
name: portfolio-construction-analyzer
description: "Evaluate explicit long-only candidate portfolios against position, group, risk and liquidity constraints, and validate supplied optimization-result provenance. Does not manufacture an optimized portfolio or trade."
license: MIT
compatibility: Python 3.10+ offline supplied JSON. Engines, data rights and professional acceptance are deployment dependencies.
metadata:
  aws-fsi-category: "Asset Management"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 7 - asset management foundations"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (MNPI / client-confidential)"
  aws-fsi-jurisdictions: "Explicit supplied scope; no universal jurisdiction pack"
  aws-fsi-owner: "Asset Management investment & product"
  aws-fsi-primary-user: "Institutional investment professional / control reviewer"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-09-21"
---

# Portfolio construction review

Use this package when the requested job is to evaluate explicit long-only candidate portfolios against position, group, risk and liquidity constraints, and validate supplied optimization-result provenance. Does not manufacture an optimized portfolio or trade.

Read [input and method rules](references/domain-rules.md) before constructing the native request;
[the source map](references/source-map.md) distinguishes supplied assertions from authoritative evidence.
Use [handoffs](references/handoffs.md) for adjacent jobs and [controls](references/controls.md) for review limits.

1. Establish the institution/portfolio identity, currency, economic date, knowledge cutoff and professional role.
2. Obtain the supplied policy/model/holdings inputs listed in the schema. Missing facts remain unknown; never invent a rate, exposure, legal classification or approval to complete a request.
3. Run `python scripts/validate_input.py INPUT.json`, then `python scripts/calculate_or_transform.py INPUT.json`. Rejected sources require corrected evidence. Review gaps remain visible in the draft.
4. Reconcile the results to independently sourced benchmarks or manual calculations using the documented method. An unavailable engine is an explicit gap; do not replace it with a simplified undisclosed model.
5. Run `python scripts/validate_output.py OUTPUT.json --input INPUT.json` against the separately retained original. This binds supplied inputs and outputs without authenticating their truth.
6. Prepare the [review packet](assets/output-template.md), retain unresolved issues and obtain the named professional review. The native result is immutable; any narrative or publication projection needs separate evidence review.

Do not use this package to perform trades, approve a policy, determine personal tax advice,
certify compliance, publish claims or write a system of record. It creates an internal draft.
Its concrete method is `long-only-candidate-feasibility`. Limitations: Annualized supplied covariance; PSD tolerance1e-30 and analytic volatility rounded12places. No shorting/leverage, nonlinear derivatives, liability optimization or solver; expected returns are assumptions.

Run `python scripts/selftest.py` for independently expected arithmetic and boundary cases.
Generated helpers are pinned by the repository's shared-resource lock; do not edit bundled copies.
