---
name: prompt-and-agent-risk-reviewer
description: >-
  Review an LLM agent or prompt configuration for risk before deployment: examine the system
  prompt/instructions, tools and permissions, memory, retrieval/RAG sources, guardrails,
  failure modes, prompt-injection exposure, and prohibited-behavior surfaces, then produce
  cited findings mapped to a control catalog with a recommended risk rating and disposition.
  Use when an AI security, AI governance, or skill owner asks "review this agent for risk",
  "check this prompt/agent for prompt-injection exposure", "is this agent configuration safe
  to deploy", "what controls are missing", or needs a review-ready findings pack before an
  AI risk-committee adjudication. This skill evidences findings and recommends a rating for a
  human adjudicator; it NEVER approves an agent for deployment, accepts risk, grants an
  exception, attests a control, files to the risk register, or closes the review — those are
  human/authorized-system actions.
license: MIT
compatibility: Amazon Quick Desktop; requires agent/prompt-registry, control-catalog/AI-policy, model-registry/data-catalog, agent-tool-logs/evaluation-harness, and risk/issue MCP integrations (all read-only).
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
  aws-fsi-primary-user: "AI security / AI governance / skill owner"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Prompt and Agent Risk Reviewer

## Purpose and outcome
Given a registered LLM agent/prompt configuration, evaluate it against a **versioned control
catalog** — covering prompt-injection exposure, tool/permission risk, memory, retrieval
trust, guardrails, failure modes, and prohibited-behavior surfaces — attach **cited
evidence** to each fired finding, and produce a review-ready pack with a **recommended risk
rating** and **recommended disposition**. A successful output lets the accountable AI risk
owner adjudicate whether to deploy, remediate, or reject — the decision, and any approval,
remains human.

## Use when
- "Review this agent / prompt for risk before we deploy it."
- "Check this configuration for prompt-injection exposure."
- "What controls are missing on this agent? How severe?"
- A reviewer needs a consistent, cited findings pack to attach to an AI risk-committee item.

## Do not use
- The user wants an **approval**, **risk acceptance**, **exception**, **attestation**, or
  the **review closed** → out of scope; produce findings and route to the human adjudicator.
- Build the **formal AI risk assessment / register entry** → `ai-risk-assessment-builder`.
- A deep, standalone **least-privilege review of tool entitlements/OAuth scopes** →
  `agent-permission-scope-reviewer`.
- Design the **evaluation/benchmark suite** for the eval gap → `ai-evaluation-benchmark-builder`.
- Review **runtime audit trails** of a deployed agent (what it actually did) →
  `agent-audit-trail-reviewer`.
- Investigate an **AI incident** that already occurred → `ai-incident-investigator`.
- Assess the impact of a **spec change** → `model-change-impact-analyzer`.
- Validate a statistical/ML **model** (not an agent/prompt) → `model-validation-assistant`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a findings pack with a
durable `review_id`; downstream assessment/permission/eval/incident skills consume it. It
must not duplicate their work or make the deployment decision.

## Inputs and prerequisites
- The **agent review package**: the agent/prompt spec (system prompt summary, `autonomy`,
  `data_classification`, tools with effects/scopes/approval flags, `untrusted_input_surfaces`,
  memory, retrieval sources with trust, guardrails, prohibited surfaces, failure mode,
  observability) plus `control_catalog_version`. Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Read access to the agent/prompt registry, control catalog/AI policy, model/data catalog,
  logs/eval-harness coverage, and risk/issue systems (all read-only).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The registered agent spec is the
object of record; the control catalog supplies the checklist, severities, and mapping;
registry/catalog supply data classification and ownership. Cite every finding to a
configuration locus. Undocumented controls are treated as **not evidenced** (gaps), never
assumed present.

## Workflow
1. **Scope & validate** — confirm the agent, revision (`as_of`), and
   `control_catalog_version`; run [scripts/validate_input.py](scripts/validate_input.py);
   record absent control blocks as `data_gaps`.
2. **Evaluate controls (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to evaluate each
   catalog control (injection exposure, tool risk, memory, retrieval trust, guardrails,
   least privilege, failure mode, eval/logging coverage). Each fired finding returns its
   severity and the evidence loci behind it. Findings are **explainable**, not a black-box
   score.
3. **Assemble evidence** — for each fired finding, attach the specific configuration loci
   and the remediation guidance, with citations.
4. **Recommend rating & disposition** — map the fired-finding severities to a
   **recommended risk rating** (Critical/High/Moderate/Low) and a **recommended disposition**
   per the documented mapping. This is a recommendation for a human adjudicator, explicitly
   **not** an approval or a binding decision.
5. **Write the pack** — plain-language finding-by-finding explanation + evidence + the
   recommended rating/disposition + `data_gaps` + reviewer prompts (compensating controls,
   blast radius) + the standing disclaimer.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check confirms: every fired finding has a control_id + cited evidence +
remediation, the rating and disposition tie out to the deterministic mapping, no
approval/risk-acceptance/attestation/closure language is present, and the standing disclaimer
and human-adjudication note are included. Fail closed on any miss.

## Human approval
`required`: a human adjudicator (accountable AI risk owner) must decide before any
deployment, risk acceptance, exception, attestation, or review closure. The skill produces
findings and a recommendation; it never approves, accepts risk, attests, files, or closes.

## Failure handling
- **Undocumented controls** (missing memory/guardrails/observability blocks) → treat as
  controls-not-evidenced; the dependent findings fire and the gap is listed in `data_gaps`;
  never assume a control is present.
- **Ambiguous agent/revision** → stop and confirm; never review the wrong revision.
- **Spec vs design-doc conflict** → cite both; do not resolve silently.
- **Embedded secret in a prompt** → redact it and raise it as a finding; never echo it.
- **Tool timeout** → return partial findings computed so far with a clear "incomplete" flag;
  no retry assumption.

## Output contract
1. **Summary** — agent, revision (`as_of`), `control_catalog_version`, fired-finding count by
   severity, recommended rating, recommended disposition.
2. **Findings** — per fired finding: `control_id`, title, severity, plain-language rationale,
   cited evidence loci, and remediation guidance.
3. **Data gaps** — absent control blocks the review treated as gaps.
4. **Reviewer prompts** — compensating controls, blast radius, and adjudication questions.
5. **Machine-readable** — findings + evidence + `review_id` for downstream skills.
6. **Standing disclaimer** — "Risk review evidence and recommendations only; not an approval,
   risk acceptance, or attestation. Deployment requires human adjudication by the accountable
   AI risk owner."
See [references/controls.md](references/controls.md) and
[references/domain-rules.md](references/domain-rules.md).

## Privacy and records
**Confidential.** The review reasons over configuration, not customer data; do not paste live
secrets, tokens, or customer PII into the review. Redact any embedded secret found in a
system prompt and flag it. Retain the review + citations + `control_catalog_version` per
records policy; log the read and the routing of recommendations to the human adjudicator.

## Gotchas
- **A finding is not a decision.** Findings and a recommended rating justify *adjudication*,
  never an approval, risk acceptance, attestation, or review closure.
- **Missing control = gap, not pass.** An undocumented guardrail/memory/logging block is
  treated as absent (the finding fires); this is deliberate — false negatives are the
  dangerous class in a risk review.
- **Injection needs a reachable path.** `C-INJ-01` fires only when untrusted input can reach
  a high-impact tool; note in reviewer prompts whether that path is truly reachable at
  runtime or blocked by a compensating control.
- **Least privilege is judged against declared purpose.** `scope_broad` reflects scope vs.
  the stated purpose, not a guess about what the agent "should" have.
- **Catalog is versioned.** Record `control_catalog_version` on every review so the rating is
  reproducible and reviewable; never tune severities to make an agent pass.
