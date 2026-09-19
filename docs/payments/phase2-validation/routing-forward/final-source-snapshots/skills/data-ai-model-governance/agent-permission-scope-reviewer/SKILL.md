---
name: agent-permission-scope-reviewer
description: >-
  Review an AI agent or skill's declared tool-and-operation permission scope against
  least-privilege governance: map each operation to its user need, data classification,
  access mode, approval gate, audit logging, segregation of duties, and
  revocation/recertification, then surface least-privilege findings with cited evidence and
  a recommended disposition. Use when an IAM, AI-governance, or security-architecture
  reviewer asks "is this agent's scope least-privilege", "review the tool permissions for
  this agent/skill", "check this permission manifest before we grant it", or needs an
  evidence-backed scope-review pack before an access decision. This skill evidences findings
  and recommends remediation for human adjudication; it NEVER grants, denies, provisions, or
  revokes access, approves an agent for production, closes the review, or files a
  waiver/exception — those are human/authorized-system actions.
license: MIT
compatibility: Amazon Quick Desktop; requires model-registry, data-catalog, agent/tool-log, IAM/entitlement, policy-retrieval, and evaluation-harness MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Data, AI & Model Governance"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 1 - platform controls"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Confidential"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "AI / Model Risk Governance"
  aws-fsi-primary-user: "IAM / AI governance / security architecture"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Agent Permission Scope Reviewer

## Purpose and outcome
Given an agent's (or skill's) **declared permission manifest** — the set of tools and
operations it requests, each with an access mode, data classification, approval gate,
logging, segregation group, and revocation terms — apply the versioned least-privilege
control ruleset to every operation, surface **least-privilege findings** with cited
evidence, and produce a review pack with a **recommended disposition**. A successful output
lets an IAM / AI-governance / security-architecture adjudicator decide whether to approve,
condition, or reject the scope. The decision, and any entitlement grant/revocation, remains
a human/authorized-system action.

## Use when
- "Is this agent's scope least-privilege?" / "Review the tool permissions for this skill."
- "Check this permission manifest before we grant the entitlements."
- "Which operations here are over-scoped, unlogged, or missing an approval gate?"
- A control owner needs a consistent, cited scope-review pack to attach to an access request
  or an AI-system risk record before adjudication.

## Do not use
- The user wants the scope **approved/denied**, an entitlement **granted/revoked/provisioned**,
  the agent **cleared for production**, the review **closed**, or a **waiver/exception filed**
  → out of scope. Provide the review pack and route to the human adjudicator / IAM system.
- **Prompt, instruction, memory, retrieval, and guardrail content review** (prompt-injection
  exposure, prohibited-behavior review) → `prompt-and-agent-risk-reviewer`.
- **Building the evaluation/benchmark suite** for an agent → `ai-evaluation-benchmark-builder`.
- **Model-registry inventory / model-risk documentation** (SR 11-7 style) → the model
  inventory / model-risk-documentation skills, not this one.
- General "what can this agent do" explainer with no least-privilege question → route to the
  relevant domain explainer.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a scope-review pack
with a durable `review_id`; downstream adjudication, risk-acceptance, and access-provisioning
systems consume it. It must not duplicate their approval or provisioning steps.

## Inputs and prerequisites
- The agent/skill **permission manifest**: `agent_id`, `as_of`, `policy_version`,
  `environment`, and `operations[]`. Each operation carries `op_id`, `tool`, `operation`,
  `access_mode`, `data_classification`, and (drives findings) `declared_need`, `writes`,
  `logged`, `approval_gate`, `revocation`, `segregation_group`, `justification_ref`.
  Schema: [scripts/validate_input.py](scripts/validate_input.py).
- The **least-privilege control policy** version in force (thresholds and the approved rule
  set): [references/domain-rules.md](references/domain-rules.md).
- Read access to the model registry, data catalog, agent/tool logs, and IAM/entitlement
  system to confirm declared values against reality (see
  [references/source-map.md](references/source-map.md)).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The IAM/entitlement system is the
position of record for what is actually granted; the manifest is the *request*; the data
catalog classifies each data source; agent/tool logs evidence whether logging is real. Cite
every finding to a specific manifest field, policy rule, or system record. Where the manifest
and the system-of-record disagree, cite both and flag the conflict — never silently reconcile.

## Workflow
1. **Scope & load** — confirm the agent/skill under review, its `environment`, and the
   `policy_version`; load the manifest; validate with `validate_input`.
2. **Apply the ruleset (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to evaluate every
   operation against the seven least-privilege dimensions (need, classification, least
   privilege / access mode, approval gate, logging, segregation of duties, revocation) using
   the versioned rules. Each fired rule returns a finding with a severity, the evidence
   behind it, and a recommended remediation.
3. **Assemble evidence** — for each finding, attach the specific manifest field(s) and the
   policy rule it violates, with citations. Mark operations missing required fields as
   `not_evaluable` for the affected dimensions rather than guessing.
4. **Recommend a disposition** — map the finding-severity profile to a recommended
   disposition band (Remediate-before-approval / Conditional / Review-minor / No-exceptions)
   per the documented mapping. This is a **recommendation for a human adjudicator**, not an
   access decision.
5. **Write the pack** — per-operation findings + evidence + recommended remediation + the
   recommended disposition + explicit not-evaluable gaps + the standing disclaimer.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check confirms: every finding uses an approved rule id and has ≥1 cited
evidence row, the recommended disposition maps deterministically from the findings, no
autonomous approval/denial/provisioning/closure/filing language is present,
`human_adjudication_required` is true, and the standing disclaimer is present. Fail closed on
any miss.

## Human approval
`required` (R3): a human adjudicator must approve, condition, or reject the scope before any
entitlement is granted, revoked, or provisioned, before the agent is cleared for an
environment, and before the review is closed or a waiver/exception is filed. This skill never
performs those actions; it recommends and evidences only. No approval is needed for the
reviewer's own read of the pack.

## Failure handling
- **Missing manifest fields** (no `approval_gate`, `logged`, `data_classification`, …) →
  mark the affected dimension `not_evaluable`; do not assume a safe default.
- **Ambiguous agent/manifest identity** → stop and confirm; never review the wrong scope.
- **Manifest vs. system-of-record conflict** (e.g., manifest says logged, logs show none) →
  cite both, raise the conflict as a finding; do not resolve silently.
- **Stale policy version** → state that findings are bound to the loaded `policy_version`;
  do not back-date a newer rule onto an older request without saying so.
- **Tool timeout / partial manifest** → return the findings computed so far with a clear
  `incomplete` flag; never imply the review is complete.

## Output contract
1. **Summary** — agent (id), environment, operations reviewed, counts by severity,
   recommended disposition band.
2. **Findings** — per finding: `rule_id`, operation, dimension, severity, plain-language
   reason, cited evidence row(s), and a recommended remediation.
3. **Not-evaluable** — operations/dimensions that could not be assessed and why.
4. **Recommended disposition** — deterministic band + `human_adjudication_required: true`.
5. **Machine-readable** — findings + evidence + `review_id` for downstream adjudication.
6. **Standing disclaimer** — "Least-privilege review evidence only; not an access approval or
   denial. No entitlement has been granted, revoked, or provisioned, and no review has been
   closed. Human adjudication is required."
See [references/controls.md](references/controls.md).

## Privacy and records
Confidential. The manifest describes system entitlements, not customer data; do not pull
sample records from the reviewed data sources. Record the review, findings, citations, and
`policy_version` per records policy; log the read and any downstream adjudication reference.
Never exfiltrate manifest or entitlement detail beyond the review pack.

## Gotchas
- **A finding is not a decision.** Even zero findings do not "approve" a scope — human
  adjudication is still required; the pack says so.
- **Read the mode, not the label.** An operation labelled read-only that carries `writes:
  true` or `access_mode: auto-write` is a write; evaluate the effective mode, not the name.
- **Segregation is agent-level.** One over-permissioned operation may look fine alone; the
  SoD conflict appears only when the agent holds write *and* approve duties together.
- **Undeclared classification is scope creep.** An operation touching a data classification
  not listed in the manifest's declared scope is a finding, not a rounding error.
- **Bind to the policy version.** Thresholds and the rule set come from the versioned policy,
  never from guessing "what feels least-privilege"; the pack records the version used.
- **Manifest ≠ reality.** The manifest is a request; confirm logging, classification, and
  actual grants against the systems of record before relying on a declared value.
