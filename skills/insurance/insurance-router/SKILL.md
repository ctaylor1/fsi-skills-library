---
name: insurance-router
description: "Route insurance work by participant, line and recurring job to installed operating, specialist, parametric, health-payer and shared architecture workflows. Preserve native input, source, identity and authority boundaries; expose unsupported profiles without substituting unrelated methods."
license: MIT
compatibility: Python 3.10+; offline explicit-intent routing.
metadata:
  aws-fsi-category: "Insurance"
  aws-fsi-skill-type: "Workflow or orchestration skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Orchestrate & resolve"
  aws-fsi-agent-pattern: "Interactive workflow copilot"
  aws-fsi-delivery-wave: "Insurance Phase 5"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Confidential; minimize policy and claim identifiers"
  aws-fsi-jurisdictions: "Reviewed target-specific jurisdiction/product profiles required; fixture coverage is not global applicability"
  aws-fsi-owner: "Insurance architecture and workflow governance"
  aws-fsi-primary-user: "Insurance practitioners, operations, product, risk and technology teams"
  aws-fsi-version: "0.6.0"
  aws-fsi-recertification-date: "2027-10-04"
---

# Insurance workflow routing

Identify the requested work product, represented party, practitioner capacity,
business object, line of business, jurisdiction and requested action. Ask only for
context that changes ownership or applicability; a missing fact remains unknown.
For a clear single task, load the specialist directly. For several requested jobs,
prepare separate scoped routes with one accountable owner for each deliverable.

Select the explicit intent in [references/routes.json](references/routes.json).
The script does not classify natural language. Run
`python scripts/route.py REQUEST.json` and validate the retained routing artifact
with `python scripts/route.py --validate ROUTE.json`. The optional
`available_skills` list is the deployment inventory. Without it, availability is
unverified; a catalog target does not prove installation or source access.
Read [references/source-map.md](references/source-map.md) for the input vocabulary
and [references/controls.md](references/controls.md) for source/access boundaries.

## Ownership distinctions

- Rating uses supplied approved rates/factors. P&C rate adequacy has a separate
  bounded indication workflow using reviewed ultimate losses and assumptions.
  Loss reserving and long-duration liability valuation remain different methods.
- Policy explanation is not a post-loss coverage analysis. Prospective coverage
  gaps use stated needs, not claim facts. P&C claim coverage reviews clause/fact
  hypotheses; case financial scenarios have their own owner and do not select reserves.
- Claim intake retains receipt even when incomplete. Carrier triage is distinct
  from claimant document preparation. File QA and cost reconciliation do not
  determine coverage, liability, damages or settlement value. Handling plans and
  payment/closure review preserve outstanding evidence and actual payment state.
- Health-member appeals must use the health profile. P&C/life claimant disputes
  are not silently translated into medical-necessity appeals.
- One policy form comparison belongs to policy wording; treaty interpretation and
  comparison belong to reinsurance contract review, which owns its terminology.
- A single claim's SIU referral belongs to fraud referral review. Portfolio exact-identifier
  pattern review and case-level SIU investigation now have separate native packages;
  signals are not proof of fraud and a referral is not an investigation.
- A current event alert belongs to CAT monitoring. Ceded program comparison uses
  supplied event scenarios and reviewed layers. Exposure aggregation and supplied CAT
  loss-table analysis have native packages; hazard/vulnerability model generation
  and scientific validation are not inferred from those calculations.
- Policy transactions, premium billing, producer onboarding, placement and
  delegated authority each own their native evidence and state checks. A license
  does not grant binding authority; a past-due balance does not establish lapse.
- Life evidence/referral, life/annuity sales, value-affecting contract service and
  death-benefit preparation are separate workflows. Disability, long-term-care
  and health-payer profiles are not supplied by the life underwriting package.
- Experience, life cashflow pricing, liability valuation and ALM use distinct
  bounded methods. Finance close, capital ratio scenarios and ORSA preparation do
  not supply a statutory reserve engine or regulatory approval. Disability/LTC
  benefit review is carrier-owned; its claimant appeals route to dispute preparation.
- Consumer, insurer, producer, claimant and SIU roles are not interchangeable
  access profiles. Routing never grants authority to share their source records.

- Workflow/data/core design and shared architecture, automation economics, data value
  and queue performance are draft review capabilities. Supply measured evidence and
  explicit failure paths; designs and positive projections do not activate workflows.

- Parametric trigger scenarios require final contract-designated index evidence; CAT alerts alone do not supply it.
- Health payer pricing, utilization evidence, coded-claim payment review and network access review have separate owners. Member appeals remain member-owned. These supplied-rule workflows do not supply individual health underwriting, clinical decisions or adopted regional rules.

## Route outcomes and handoffs

`routed` selects an existing catalog capability; `needs-clarification` identifies
missing capacity/line/intent; `capability-gap` retains unsupported work;
`target-unavailable` identifies missing deployment packages; `action-unavailable`
retains execution requests. Do not substitute a nearby skill for a gap.
Supporting skills are suggestions for relevant evidence, never automatic tasks.

Follow [references/handoffs.md](references/handoffs.md) and
[references/insurance-contract.md](references/insurance-contract.md). A route is
not target input. Native target validation, identity/access review and unresolved
finding retention remain required. The optional `scripts/validate_handoff.py`
dispatches legacy insurance and portable workflow evidence contracts and checks a handoff against an explicitly supplied installed package root; it executes
only that trusted package's local input validator, never a business action.

Use [references/migrations.json](references/migrations.json) for old skill names.
Aliases select current job owners only; old input schemas are not automatically
compatible. A generic actuarial-model-run request needs an explicit actuarial
purpose, and a generic claim appeal needs its actual line.

Run `python scripts/test_routing.py`. Natural-language cases in
[evals/evals.json](evals/evals.json) remain model-evaluation specifications until
actually exercised. Structural routes alone do not prove professional quality.
