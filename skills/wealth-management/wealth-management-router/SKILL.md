---
name: wealth-management-router
description: Route explicit wealth-advisor requests across P0 client foundations, P1 planning/investments, P2 practice/client development and specialized investments, and P3 family governance and trust administration. Use for multi-step or ambiguous wealth workflow selection; routing does not execute a workflow or approve an action.
license: MIT
compatibility: Python 3.10+ for deterministic routing; target skills must be installed separately. No connectors or external actions.
metadata:
  aws-fsi-category: "Wealth Management"
  aws-fsi-skill-type: "Workflow or orchestration skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Orchestrate & resolve"
  aws-fsi-agent-pattern: "Interactive workflow copilot"
  aws-fsi-delivery-wave: "Wave 9 - wealth management P3"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "existing-updated"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Wealth Management advisory & compliance"
  aws-fsi-primary-user: "Wealth advisor / client-service associate"
  aws-fsi-version: "0.4.0"
  aws-fsi-recertification-date: "2027-09-17"
---

# Wealth management workflow routing

Use this entrypoint when the request spans several wealth workflows or the correct specialist is unclear. For a clear single task, load its skill directly.

1. Identify the practitioner capacity, subject (household, prospect, book, family group or trust), jurisdiction and requested deliverable. Do not equate an advisory engagement with a brokerage account or apply one legal standard across them. If scope is ambiguous, ask the smallest necessary clarification while preparing the known context.
2. Select only requested intents from [references/domain-rules.md](references/domain-rules.md). The script accepts explicit intents, not natural-language legal interpretation. When financial exploitation concerns are present, prioritize the protection screening handoff and human escalation under firm policy. Do not diagnose capacity or impose holds.
3. For a structured routing artifact, follow [references/source-map.md](references/source-map.md), then run `python scripts/route.py INPUT.json > OUTPUT.json` and `python scripts/route.py --validate OUTPUT.json`.
4. Load only the selected target skill and relevant resources. Use [references/handoffs.md](references/handoffs.md) to prepare the target input. Preserve source IDs and unresolved findings; validate the target independently. A route is not an instruction to complete unrequested steps.
5. Return the route, evidence required and remaining human decisions. This router does not launch tools, execute trades, open accounts, deliver messages or change records. Read [references/controls.md](references/controls.md) for deployment limits.

`review-ready` means the routing artifact is complete; it says nothing about the target workflow or recommendation readiness. Unsupported and action-taking intents remain visible and require clarification or an authorized professional workflow.

Run `python scripts/test_routing.py`; [evals/evals.json](evals/evals.json) separates executable checks from natural-language cases.

Book review uses an explicit advisor-book collection scope. Preserve actual household IDs on each action and prepare separate client/prospect target requests; a book identifier cannot establish a client relationship.

Family governance and trust administration require their own explicit subject scopes. Family membership does not establish trust powers, beneficiary entitlement or permission to share records. Prepare a distinct target request with a reviewed identity mapping; neither family nor trust markers are actual household identifiers.
