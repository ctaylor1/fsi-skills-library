---
name: ai-use-case-intake-classifier
description: >-
  Classify a proposed AI, ML, GenAI, or agent use case by purpose, user populations, autonomy,
  decision effect, data sensitivity, materiality, jurisdictions, model type, third-party exposure,
  and prohibited-practice indicators, then map the fired risk factors to a governance tier and a
  recommended governance path with cited evidence. Use when someone submits an AI/agent intake or
  asks "which governance review does this use case need", "what risk tier is this AI use case",
  "triage this AI intake", or needs a consistent, source-linked classification to route a proposal
  to the right reviews (model risk, fairness, privacy/DPIA, legal, third-party, evaluation). This
  skill produces a PROVISIONAL classification and recommended path for human adjudication only; it
  NEVER approves, clears, exempts, waives, or closes a use case, never grants governance sign-off,
  and never makes the binding governance decision — those are human/authorized-body actions.
license: MIT
compatibility: Amazon Quick Desktop; requires model-registry, data-catalog, AI-governance-policy, evaluation-harness, and agent/tool-log MCP integrations (all read-only).
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
  aws-fsi-primary-user: "AI governance / product owner / risk"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# AI Use-Case Intake Classifier

## Purpose and outcome
Given a structured **intake submission** for a proposed AI/ML/GenAI/agent use case, compute a set
of **explainable risk factors** from the submitted attributes, attach cited evidence to each fired
factor, and map the fired-factor profile to a **governance tier** (Prohibited / High / Limited /
Minimal) and a **recommended governance path** with the specific reviews required. A successful
output lets an AI governance owner, product owner, or risk reviewer see *why* a use case lands where
it does and route it to the right reviews consistently. The classification is a **triage
recommendation for human adjudication** — the binding governance decision, any approval, exemption,
or intake closure remains with the human governance body.

## Use when
- "Which governance review(s) does this AI use case need?"
- "What risk tier is this GenAI / agent use case?"
- "Triage / classify this AI intake submission and route it."
- A governance intake queue needs a consistent, cited classification attached to each submission.
- Someone needs to know the required review gates before an AI project proceeds.

## Do not use
- The user wants the **binding governance decision, an approval, an exemption, a waiver, or intake
  closure** → out of scope. Produce the classification and route to the human governance body.
- The user wants the **full AI risk assessment** (data/model/fairness/explainability/security/
  privacy/oversight write-up) → `ai-risk-assessment-builder`.
- **Registering** the model/agent in inventory (ownership, lineage, purpose record) →
  `model-inventory-maintainer`.
- **Reviewing prompts, tools, memory, retrieval, guardrails** in depth →
  `prompt-and-agent-risk-reviewer`; **least-privilege tool/permission mapping** →
  `agent-permission-scope-reviewer`.
- **Independent model validation** → `model-validation-assistant`; **third-party provider due
  diligence** → `third-party-ai-due-diligence-assistant`; **evaluation benchmark design** →
  `ai-evaluation-benchmark-builder`.
- Investigating a live AI **incident** → `ai-incident-investigator`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a cited **classification
record** with a durable `classification_id`; downstream governance skills consume it and perform the
substantive reviews. It must not duplicate their assessment work or reach a governance decision.

## Inputs and prerequisites
- An **intake submission** (JSON) describing the proposed use case: `use_case_id`, `title`, `as_of`,
  `config_version`, `purpose`, `user_populations`, `autonomy`, `decision_effect`, `model_type`,
  `external_provider`, a `data` block (personal / special-category / classification /
  affected_individuals), `materiality`, `jurisdictions`, and any `prohibited_practice_indicators`.
  Schema: [scripts/validate_input.py](scripts/validate_input.py).
- Read access to the **AI-governance policy/ruleset** (versioned thresholds and mappings — see
  [references/domain-rules.md](references/domain-rules.md)), and to the model registry / data catalog
  to corroborate submitted attributes.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The **AI-governance policy/ruleset**
(versioned config) is the position of record for the classification rules and thresholds; the
**intake submission** supplies the facts being classified; the **model registry / data catalog**
corroborate data classification, model type, and lineage. When the submission conflicts with the
catalog (e.g., self-declared data class), cite both and flag for adjudication — never silently trust
the submitter over the catalog.

## Workflow
1. **Scope & validate** — confirm the submission and its `config_version`; run `validate_input` and
   resolve structural errors before classifying. Note which factors are *not evaluable* from the data.
2. **Compute factors (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to evaluate the configured
   risk factors (regulated decision, autonomous action, customer/public-facing, special-category
   data, personal-data-at-scale, high materiality, cross-border, third-party model, GenAI/agentic,
   prohibited-practice). Each fired factor returns its reason, the evidence field(s), and a citation.
3. **Map to tier & path** — the fired-factor set maps deterministically to a governance tier and a
   recommended governance path per the documented mapping. Derive the specific `required_reviews`.
4. **Assemble the record** — plain-language explanation per fired factor + evidence + tier + path +
   required reviews + explicit open questions / not-evaluable factors + the human-adjudication flag.
5. **Route** — hand the record and `classification_id` to the human governance body and the
   downstream review skills; do not decide.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py) after. The
output check confirms: every fired factor has cited evidence; the governance tier and path equal the
deterministic mapping from the fired factors; `human_adjudication_required` is `true`; no binding
governance decision / approval / clearance / exemption / closure language is present; and the
standing disclaimer is included. Fail closed on any miss.

## Human approval
`required` (R3): the classification is decision **support**. A human governance body must adjudicate
the tier and path, and no approval, exemption, waiver, or intake closure occurs without that human
decision. The skill never grants sign-off, never clears a use case for deployment, and never closes
the intake.

## Failure handling
- **Missing / ambiguous attributes** (e.g., no materiality block, data class not stated) → mark the
  dependent factors `not_evaluable`; classify on what is present and list the gaps; do not guess.
- **Submission vs. catalog conflict** → cite both, flag for adjudication, and classify at the more
  conservative value (fail safe upward, never downward).
- **Unknown / unsupported jurisdiction** → flag it; apply the US default pack and note the missing
  jurisdiction pack rather than assuming coverage.
- **Prohibited-practice indicator present** → tier is `Prohibited`; route to Legal/Ethics escalation;
  the skill does not clear it.
- **Stale config version** → record the version used; if the ruleset is expired, flag it and do not
  silently substitute a newer one.
- **Tool timeout** → return the factors computed so far with a clear "incomplete" flag; do not emit a
  tier from a partial evaluation.

## Output contract
1. **Summary** — use case (id, title), `as_of`, config version, count of fired factors, governance
   tier, recommended governance path.
2. **Factors** — per fired factor: name, plain-language reason, evidence field(s) with citation, and
   weight.
3. **Required reviews** — the specific downstream review gates the tier/path demands.
4. **Open questions / not-evaluable factors** — attributes missing or conflicting.
5. **Machine-readable** — factors + evidence + tier + path + `required_reviews` +
   `human_adjudication_required: true` + `classification_id` for downstream skills.
6. **Standing disclaimer** — "Provisional classification prepared for human governance adjudication
   only; it does not grant, waive, exempt, or close any governance review, and is not a deployment
   authorization."
See [references/controls.md](references/controls.md).

## Privacy and records
`Confidential`. The intake describes a *proposal*, not customer records; keep submitter identity to a
role, not a named individual, and do not pull customer NPI/PII into the classification — reference the
data *classification*, not the data. Retain the classification + citations + config version per
records policy; log the read and the routing. Never exfiltrate the submission.

## Gotchas
- **A classification is not a decision.** A "High" tier means *more review is required*, never that
  the use case is approved, cleared, or blocked. Approval and closure are human-adjudicated.
- **Conservative on conflict.** If the submitter's data class disagrees with the data catalog, take
  the higher sensitivity; a mis-declared low class must not down-tier a use case.
- **Prohibited ≠ this skill's call.** A prohibited-practice indicator forces escalation to
  Legal/Ethics; the skill flags and routes, it does not adjudicate legality.
- **Thresholds are config, not judgment.** Materiality and scale thresholds come from the versioned
  ruleset, not from guessing what "feels" material for this use case.
- **GenAI/agentic ≠ automatically High alone.** One factor lands at "Limited"; the tier rises with
  regulated decisions, autonomy, special-category data, high materiality, or ≥3 combined factors —
  per the documented mapping, not intuition.
- **Don't infer intent from purpose text.** Classify from the declared, structured attributes and the
  catalog; do not editorialize about whether the team "really" needs the AI.
