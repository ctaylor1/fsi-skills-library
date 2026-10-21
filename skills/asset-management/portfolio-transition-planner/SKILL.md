---
name: portfolio-transition-planner
description: "Review a human-supplied staged transition of long-only cash equities or ETFs for daily participation, deliverable shares, settlement cash, target quantities and estimated costs. Use for transition feasibility review; no optimizer, order staging or execution."
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
  aws-fsi-primary-user: "Portfolio implementation / transition manager"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-10-04"
---

# Portfolio Transition Planner

Prepare a draft transition feasibility packet from the supplied current settled book, target quantities and human-defined trade slices. Read [domain rules](references/domain-rules.md) before treating planning estimates as cost or funding evidence.

Establish the exact portfolio and account scope, review snapshot, single currency, transition horizon, target authority and accountable owner. Obtain current settled cash and freely deliverable quantities. Separate market-volume forecasts and estimated execution prices from actual observations. Read [schema](references/schema.md) to map all outcome-relevant records with source references.

Review the supplied schedule for gross same-security daily participation, oversells, security deliveries, settlement cash before same-day receipts, estimated explicit fees and unreached targets. When a breach appears, preserve the proposed schedule and ask its accountable owner for a revised scenario; never silently optimize or stage orders. The cash and share conventions are conservative daily checks and do not establish intraday settlement readiness.

Run input validation, calculation and detached-original output validation. Use the [output template](assets/output-template.md) to explain the binding constraints, alternative human-supplied scenarios, dependencies and next review. Check [source map](references/source-map.md), [controls](references/controls.md) and [handoffs](references/handoffs.md) for professional boundaries.

No transition manager selection, trade execution, legal settlement rule, tax-lot choice, mandate approval or external communication is performed. A passing schedule candidate is an internal arithmetic result; portfolio, trading and operations owners retain acceptance and execution authority.

Run `scripts/validate_input.py INPUT`, `scripts/calculate_or_transform.py INPUT`, then `scripts/validate_output.py OUTPUT --input INPUT`. Retain the original separately.
