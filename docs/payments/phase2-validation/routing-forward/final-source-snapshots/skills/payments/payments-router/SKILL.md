---
name: payments-router
description: Select the accountable payment workflow for a request, distinguishing participant, rail, jurisdiction, lifecycle stage and requested deliverable. Use for ambiguous or multi-step payment requests. Reports missing capabilities instead of routing to unimplemented strategy, design or execution skills.
license: MIT
compatibility: Python 3.10+ for structured routing; target packages must be installed separately. Offline analysis only; no connectors bundled.
metadata:
  aws-fsi-category: "Payments"
  aws-fsi-skill-type: "Workflow or orchestration skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Orchestrate & resolve"
  aws-fsi-agent-pattern: "Interactive workflow copilot"
  aws-fsi-delivery-wave: "Payments Phase 1"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "none"
  aws-fsi-data-classification: "Confidential; minimize payment identifiers"
  aws-fsi-jurisdictions: "Global routing; target-specific approved jurisdiction profiles required"
  aws-fsi-owner: "Payments architecture and operations"
  aws-fsi-primary-user: "Payment product, operations, risk and technology teams"
  aws-fsi-version: "0.2.0"
  aws-fsi-recertification-date: "2027-09-17"
---

# Payments workflow routing

Identify the requested work product before selecting a skill. Determine the
participant role, rail, jurisdiction, relevant lifecycle stage and whether the
request is analysis, drafting or an action. Do not infer payment authority from
authentication, account access, a request-for-payment, a case ID or a prior output.

Use [references/routes.json](references/routes.json) for the supported intent
registry. Select an intent from the actual request; the deterministic script does
not classify natural language. A clear single-workflow request can use its target
directly. For mixed requests, identify one lead and make separate scoped handoffs;
do not launch a standard pipeline of unrequested tasks.

Run `python scripts/route.py INPUT.json` for a structured route. Inputs are
`intent`, optional `participant`, `rail`, `jurisdiction`, `requested_action`
(analyze or draft), and an optional list `available_skills` from the deployment's
installed inventory. Run `python scripts/route.py --validate OUTPUT.json` to check
the output against its retained request and registry. This establishes routing
consistency, not target readiness, domain correctness or authority.

## Boundaries that determine the lead

- One payment's state: lifecycle diagnosis. Portfolio authorization decline or
  chargeback spike: performance analysis remains a Phase 3 gap, not a single-case job.
- Merchant/acquirer representment: merchant chargeback response. Issuer or bank
  consumer error: issuer dispute review. An unknown dispute role needs clarification.
- Transaction-record matching: transaction reconciliation. Settlement/funding
  obligation: settlement reconciliation. Explain one payout using its explain-payout
  mode; do not require bank/ledger evidence or imply reconciliation assurance.
- Correct an established defect: repair planning after exception investigation.
  Ordinary refund/return/cancel: use payment-servicing-planner. Do not
  borrow repair authority for it or promise a settled payment can be rolled back.
- APP/scam payment investigation stays with payment fraud. Email compromise can
  require the cyber specialist; a phone scam does not require an email artifact.
- PCI evidence is owned by the cybersecurity package. Financial-crime adjudication
  stays with shared financial-crime specialists; payments provides event context.

## Gaps and future capabilities

The registry's `planned` entries describe coverage gaps, not installed handoffs.
Return status `capability-gap`, keep the requested work visible and explain which
existing evidence tasks can help without pretending they complete the job.
Explicit execution requests return `action-unavailable`; this router cannot make
payments, file disputes, release holds, approve repairs or change systems.

Follow [references/payment-contract.md](references/payment-contract.md) for evidence,
identity and handoff semantics. Preserve unresolved issues and validate each target's
native input. Existing integrations mentioned in older packages are expected data
sources, not bundled connections. Run `python scripts/test_routing.py` for structured
regressions. [evals/evals.json](evals/evals.json) separately retains natural-language
behavior cases; command checks do not prove those cases passed.

## Phase 2 core routes

Use bank-payment-workflow-designer for rail/design choices;
payment-initiation-control-reviewer for exact new instructions; and
payment-regulatory-applicability-reviewer for entity/activity obligations.
Merchant-acceptance strategy and payment-provider evaluation lead commercial
choices, payment-economics-modeler leads explicit prospective scenarios, and
merchant-payment-cost-analyzer retains observed-cost ownership.
Card-program-designer and card-lifecycle-operations-assistant cover issuer program
and operational-state work. A bank-rail comparison does not include card pricing or
card-program assessment; disclose this partial scope and obtain separate provider and
economic evidence. Orchestration requires a participant before choosing merchant
acceptance (merchant/acquirer) or platform architecture (bank/issuer/processor).
Missing participant or jurisdiction in other core routes remains in missing_context;
a routed destination is preliminary until its native inputs are complete.
Payment-platform-architecture-reviewer covers the core
flow/state/control design. Validate native inputs at every handoff and preserve
unknowns; supported jurisdiction labels do not establish national or firm clearance.
