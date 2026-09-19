---
name: payment-operations-improvement-analyzer
description: Analyze payment operations queues, STP, rework, staffing and task-specific automation opportunities
  with reconciled cohorts and constrained cost, capacity and cash benefits. Produces a draft operating improvement
  and AI pilot case; never closes cases or deploys automation.
license: MIT
compatibility: Python 3.10+; standard library only. Offline supplied JSON; no connectors or production actions bundled.
metadata:
  aws-fsi-category: Payments
  aws-fsi-skill-type: Analysis and evaluation skills
  aws-fsi-risk-tier: R2
  aws-fsi-archetype: Analyze & review
  aws-fsi-agent-pattern: Interactive decision-support copilot
  aws-fsi-delivery-wave: Payments Phase 3
  aws-fsi-action-mode: Draft-only; no system-of-record change
  aws-fsi-scheduled-agent: 'no'
  aws-fsi-baseline-status: new
  aws-fsi-human-approval: external-delivery
  aws-fsi-data-classification: Confidential; opaque payment identifiers only
  aws-fsi-jurisdictions: Initial US, euro area and UK; scope-specific evidence required
  aws-fsi-owner: Payments operations and transformation
  aws-fsi-primary-user: Operations leaders, process owners and AI governance reviewers
  aws-fsi-version: 0.1.0
  aws-fsi-recertification-date: '2027-09-18'
---

# Payment operations improvement analysis

Use when a payments team needs to diagnose queues, aging, straight-through processing,
rework or an automation/AI business case. Start from case-level evidence and a single
observation period. Read [references/schema.md](references/schema.md) for the native
contract; [references/domain-rules.md](references/domain-rules.md) explains cohort and
benefit accounting. A workload estimate is not permission to automate financial decisions.

1. Establish source inventory, queue ownership and the observed time window. Deduplicate
   case identities; quarantine conflicting snapshots. Separate completed-work denominators
   from open backlog and preserve unknown effort and status.
2. Tie every opportunity to explicit completed case IDs and a task. Keep legal entity,
   team, currency and cost period consistent. Report overlaps as alternative scenarios.
3. Subtract oversight, expected error handling and technology/implementation costs.
   Separate potential capacity, assumed cash realization and net economic value. Do not
   annualize a short period or sum overlapping savings without new evidence.
4. For AI, inspect task-specific evaluation data, label maturity, error costs, quality
   thresholds, human review, model version, pilot scope and stop conditions. Produce a
   draft pilot design with accountable owners; do not recommend autonomous case closure.
5. Use [assets/output-template.md](assets/output-template.md) for the operating case and
   [references/handoffs.md](references/handoffs.md) for shared AI and model-risk work.

Run `python scripts/validate_input.py INPUT.json`,
`python scripts/calculate_or_transform.py INPUT.json > OUTPUT.json`, and
`python scripts/validate_output.py OUTPUT.json --input INPUT.json`.
Run `python scripts/test_phase3.py` for boundary regressions.

A single-payment failure belongs to `payment-lifecycle-diagnoser`; service incident
impact belongs to `payment-service-incident-investigator`. This skill changes no queue,
model, staffing plan, payment, ledger or production configuration. Read
[references/controls.md](references/controls.md), [references/source-map.md](references/source-map.md)
and [references/payment-contract.md](references/payment-contract.md) before relying on outputs.
