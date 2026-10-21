---
name: private-fund-capital-activity-reviewer
description: "Reconcile supplied LP calls, distributions and commitment changes using explicit cash direction and unfunded impacts, including declared recallable reinstatements; use for notice review without issuing payments or determining legal recallability."
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
  aws-fsi-primary-user: "LP investment operations analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-09-21"
---

# LP capital activity and unfunded review

Reconcile supplied LP calls, distributions and commitment changes using explicit cash direction and unfunded impacts, including declared recallable reinstatements; use for notice review without issuing payments or determining legal recallability.

## When to use

- Reconcile LP notice cash and unfunded movements including these explicit recallable amounts.
- Route elsewhere: Pay the capital call or decide whether the LPA legally permits recall.

## Work from the actual record

1. Establish object identity, review and knowledge dates, permitted audience, source versions, and accountable reviewer. Read [input/output schema](references/schema.md) and [bounded method](references/domain-rules.md). This is an unreleased development method; institutional acceptance is unestablished.
2. Prepare the native request from authorized original evidence. [Source map](references/source-map.md) distinguishes primary guidance from the operative contract and supplied assumptions. Preserve unknowns and open issues; never populate from an example merely to pass validation.
3. Run python3 -B scripts/validate_input.py INPUT.json and python3 -B scripts/calculate_or_transform.py INPUT.json. Local arithmetic does not fetch sources, confer permission or execute an investment action.
4. Run python3 -B scripts/validate_output.py OUTPUT.json --input INPUT.json against the retained original. This rejects modified results, extra narrative and embedded source records; hashing proves reproducibility, not truth.
5. Draft the [review artifact](assets/output-template.md) using only eligible cited outputs. Apply [controls](references/controls.md); preserve unresolved matters and follow [handoff boundaries](references/handoffs.md). Narrative review is separate from immutable native output.

## Supported method

Closing unfunded=opening+explicit increases-explicit decreases. Track calls and distributions independently; net cash to LP=distributions-calls. Compare reported closing minus calculated closing; no silent balancing item. Calls cannot increase unfunded; distributions cannot reduce unfunded. Mixed/missing currency, future events, unavailable source or unknown amount withhold the complete rollforward; known cash subtotals remain explicitly partial. No implicit recallability from a distribution label.

Do not change or approve a book, model, contract, commitment, vote, transfer or investment. A successful software check is not source authentication, legal applicability, expert acceptance or distribution permission.
