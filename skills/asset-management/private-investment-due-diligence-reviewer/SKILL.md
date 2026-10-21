---
name: private-investment-due-diligence-reviewer
description: "Review a supplied private principal transaction using sources-and-uses tie-out, simple primary common-equity ownership, scenario leverage and diligence evidence gaps; use for investment committee preparation, not issuer research extraction or investment approval."
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
  aws-fsi-primary-user: "Principal investment diligence analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-09-21"
---

# Principal private-investment diligence

Review a supplied private principal transaction using sources-and-uses tie-out, simple primary common-equity ownership, scenario leverage and diligence evidence gaps; use for investment committee preparation, not issuer research extraction or investment approval.

## When to use

- Check sources and uses, proposed primary ownership and downside leverage for this principal investment diligence pack.
- Route elsewhere: Approve the acquisition, extract all issuer research again, or issue a legal or valuation opinion.

## Work from the actual record

1. Establish object identity, review and knowledge dates, permitted audience, source versions, and accountable reviewer. Read [input/output schema](references/schema.md) and [bounded method](references/domain-rules.md). This is an unreleased development method; institutional acceptance is unestablished.
2. Prepare the native request from authorized original evidence. [Source map](references/source-map.md) distinguishes primary guidance from the operative contract and supplied assumptions. Preserve unknowns and open issues; never populate from an example merely to pass validation.
3. Run python3 -B scripts/validate_input.py INPUT.json and python3 -B scripts/calculate_or_transform.py INPUT.json. Local arithmetic does not fetch sources, confer permission or execute an investment action.
4. Run python3 -B scripts/validate_output.py OUTPUT.json --input INPUT.json against the retained original. This rejects modified results, extra narrative and embedded source records; hashing proves reproducibility, not truth.
5. Draft the [review artifact](assets/output-template.md) using only eligible cited outputs. Apply [controls](references/controls.md); preserve unresolved matters and follow [handoff boundaries](references/handoffs.md). Narrative review is separate from immutable native output.

## Supported method

Sum eligible positive funding and uses separately; show funding minus uses only if complete. Simple primary common-equity post-money ownership equals investor contribution / (pre-money equity value + all new primary equity), with no secondary, preference, option or convertible modeling. For supplied scenarios compute net debt and positive-denominator net leverage/interest coverage. Diligence status is a supplied declaration; unfilled committee topics, open/contradicted evidence and missing financial inputs remain gaps. Ratios round explicitly to 12 places.

Do not change or approve a book, model, contract, commitment, vote, transfer or investment. A successful software check is not source authentication, legal applicability, expert acceptance or distribution permission.
