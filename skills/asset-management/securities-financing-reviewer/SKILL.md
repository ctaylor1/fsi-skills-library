---
name: securities-financing-reviewer
description: "Review supplied repo cash-borrower and noncash-collateral securities-lender records for agreement-specific haircut or initial margin, simple day-count accrual, collateral allocations, recalls and repo funding. No legal netting, cash-collateral reinvestment or transaction execution."
license: MIT
compatibility: Python 3.10+ standard-library offline review; no live execution or licensed data access bundled.
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
  aws-fsi-jurisdictions: "Supplied agreement and institutional scope; no legal applicability inferred"
  aws-fsi-owner: "Asset Management investment and operations"
  aws-fsi-primary-user: "Securities financing / collateral / treasury operations"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-10-04"
---

# Securities Financing Reviewer

Prepare an agreement-bound financing control review. Identify whether each record is a repo cash-borrower or noncash-collateral securities-lender position and retain its counterparty, instrument, principal/market-value basis and accountable owner. Read [domain rules](references/domain-rules.md) before interpreting a haircut as an initial margin or a lending fee as repo interest.

Obtain the operative agreement version, supplied acceptance status, convention, effective dates, actual day-count basis and rate interval. Record current outstanding trades, collateral valuations and explicit eligibility/allocations at the same review date. Get recall notices, observed returns, available cash and committed future funding. Map the [schema](references/schema.md) without inferring netting or legal eligibility.

Run the local collateral, simple-accrual, recall and funding checks. Investigate an allocation counted twice, deficient eligible collateral, agreement gap, overdue recall or dated repayment shortfall with its owner. Missing or unsupported evidence stays unresolved; never treat a passing arithmetic comparison as a margin call, agreement enforceability conclusion or instruction to roll financing.

Run input validation, calculation and detached-original output validation. Prepare the [output template](assets/output-template.md) with transaction-level results and explicit unknowns. Use [source map](references/source-map.md), [controls](references/controls.md) and [handoffs](references/handoffs.md) for supporting evidence and related workflows.

No borrow, repo, collateral substitution, recall notice, settlement, legal opinion, financing recommendation or external message is executed. Cash-collateral reinvestment, manufactured income, rate resets, close-out calculations and cross-currency financing require another approved method.

Run `scripts/validate_input.py INPUT`, `scripts/calculate_or_transform.py INPUT`, then `scripts/validate_output.py OUTPUT --input INPUT`. Retain the original separately.
