---
name: third-party-ai-due-diligence-assistant
description: >-
  Assemble a third-party AI due-diligence package for an external AI provider or model: map
  submitted evidence to the required governance domains (viability, transparency, data
  governance, subprocessors, concentration, security, testing, contractual rights, resilience,
  exit), check coverage and freshness against the versioned rubric, tie every finding to a
  bundled evidence item, compute a deterministic residual-risk rating, and draft the pack with
  a RECOMMENDED disposition. Use when a third-party-risk, procurement, or AI-governance reviewer
  must assess or onboard an external AI/GenAI vendor, check evidence completeness (SOC 2, model
  card, DPA, eval results), or prepare a diligence pack for committee review. Keywords:
  third-party AI, vendor due diligence, model risk, concentration, subprocessor, TPRM. NEVER
  approves,
  onboards, or rejects a provider, accepts risk, signs a contract, updates an inventory, or
  asserts an unsupported finding — the recommended disposition requires human adjudication.
license: MIT
compatibility: Amazon Quick Desktop; requires AI-governance-rubric, model-registry, data-catalog, evaluation-harness, agent/tool-log, risk/issue-system, and controlled-template MCP integrations (all read-only; onboarding decision and inventory update are out of scope).
metadata:
  aws-fsi-category: "Data, AI & Model Governance"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Draft & package"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 1 - platform controls"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Confidential"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "AI / Model Risk Governance"
  aws-fsi-primary-user: "Third-party risk / procurement / AI governance"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Third-Party AI Due-Diligence Assistant

## Purpose and outcome
Turn a pile of external-AI vendor evidence into an audit-ready **due-diligence package draft**:
resolve the due-diligence domains required for the provider's criticality, confirm the
submitted evidence covers each domain and is fresh enough, tie every finding to a bundled
evidence item, compute a deterministic **residual-risk rating**, and draft a package with a
**recommended disposition** from an approved template. The outcome is a committee-ready pack
(or a clear, itemized reason it cannot be packaged yet) that a human **adjudicates**. The skill
never decides onboarding, never accepts risk, and never guarantees a provider is safe.

## Use when
- "Run third-party due diligence on this external AI vendor / model / API."
- "Assess provider X for onboarding into a production AI use case and draft the diligence pack."
- "Is the vendor's evidence complete — SOC 2, model card, DPA, eval results, audit rights, exit plan?"
- "What's the residual risk and recommended disposition for this AI provider?"

## Do not use
- Classifying the AI/agent **use case** or assigning a governance tier →
  `ai-use-case-intake-classifier`.
- **Building** an evaluation benchmark or harness (this skill consumes results) →
  `ai-evaluation-benchmark-builder`.
- Reviewing an external **agent's tool/operation permission scope** →
  `agent-permission-scope-reviewer`.
- Reviewing **prompt/agent design risk** (jailbreak, injection, unsafe tool use) →
  `prompt-and-agent-risk-reviewer`.
- Creating/updating the **model/agent inventory record** after a decision →
  `model-inventory-maintainer`.
- Any request to **approve/onboard/reject the provider, accept risk, or sign the contract** →
  refuse; draft only and route to a human.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill is due-diligence drafting
only. It consumes the classified use case (`ai-use-case-intake-classifier`), the current rubric
(`rubric_version`), registry/catalog records, and provider evidence; it emits an
`engagement_id`-keyed draft with `residual_risk_rating`, a `recommended_disposition`, and
`human_adjudication_required: true`. The onboarding decision, risk acceptance, and inventory
update belong to a human and the routed skills.

## Inputs and prerequisites
- The engagement: `engagement_id`, `provider` (`name`, `criticality`, `use_case`,
  `deployment`), an `evidence` inventory (typed items with `domain`, `ref`, `as_of`), the
  `findings` (each citing an evidence item and a severity), and optional `risk_flags`. Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- The **current** AI-governance due-diligence rubric (`rubric_version`): required domains per
  criticality, accepted evidence types, freshness windows, and the risk-flag / hard-gate rubric.
- Read access to the rubric, model registry, data catalog, evaluation harness, agent/tool logs,
  risk/issue systems, and the controlled template.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The AI-governance rubric is
authoritative for required domains, evidence, and freshness; the registry/catalog are the
records of the model and data; the evaluation harness supplies test evidence (not authored
here); provider artifacts are the submitted evidence. Cite every evidence item and the rubric.
Domains, thresholds, and gates are a **versioned contract** — record `rubric_version` on every
package.

## Workflow
1. **Validate & normalize** — run `validate_input`; confirm the engagement, evidence, and
   findings are structurally complete; flag an unclassified criticality as `needs-data`.
2. **Compute deterministically** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): required-domain
   coverage, evidence freshness, findings fidelity, and the residual-risk rating (risk flags +
   finding severity + hard gates). Rules: [references/domain-rules.md](references/domain-rules.md).
3. **Assign status** — `needs-data`, `insufficient-evidence`, `stale-evidence`, or
   `unsupported-finding` blocks packaging with an itemized reason; only a clean record becomes
   `draft-assessment`.
4. **Draft the package** — for a packageable engagement, assemble the diligence pack from
   [assets/output-template.md](assets/output-template.md): identifiers, domain coverage,
   evidence-cited findings, residual rating, recommended disposition, open gaps, and the
   reviewer adjudication block. No finding without an evidence item.
5. **Validate output** — run
   [scripts/validate_output.py](scripts/validate_output.py); fail closed on any miss.
6. **Never decide** — hand the reviewed draft to an authorized human for adjudication.

## Validation loop
Run `validate_input` before and `validate_output` after. The output screen enforces: known
criticality + rubric version; allowed status only; `human_adjudication_required: true` on every
package; a packageable record has a rubric-valid residual rating, a permitted recommended
disposition, complete domain coverage, and a non-empty fully **supported** findings index; no
approval/onboarding/risk-acceptance/contract-execution language; standing disclaimer present.
See [references/controls.md](references/controls.md). Correct and re-run until it passes or the
record is flagged not-packageable.

## Human approval
`required`. A human must **adjudicate** the recommended disposition before any onboarding
decision, risk acceptance, contract execution, or system-of-record change. This skill proposes
and drafts; it never decides, never accepts risk, and never guarantees a provider is safe. The
recommended disposition — including `do-not-proceed` — is decision support, not a decision.

## Failure handling
- **Unclassified criticality** → `needs-data`; classify the engagement first; do not assess on
  a guess.
- **Missing required domain** → `insufficient-evidence`; list the uncovered domain(s); never
  fabricate an evidence item to close a gap.
- **Stale evidence** (out of the domain's freshness window) → `stale-evidence`; request a
  refreshed artifact; never age-adjust or assume currency.
- **Unsupported finding** (cites an evidence item not in the bundle, or no findings) →
  `unsupported-finding`; drop or substantiate the claim.
- **Conflicting / superseded rubric** → return partial output with an explicit incomplete flag
  and the `rubric_version` used; no retry assumption.
- **Tool timeout** → return partial packaging with an explicit incomplete flag; do not assume a
  retry or step-up authorization.

## Output contract
1. **Package queue** — per engagement: `engagement_id`, provider, criticality, status,
   `packageable`, and (when packageable) `residual_risk_rating` + `recommended_disposition`.
2. **Due-diligence package** (per packageable engagement) — identifiers, domain coverage,
   evidence-cited findings, residual rating, recommended disposition, open gaps,
   `human_adjudication_required: true`, and `reviewer_signoff_required: true`, following
   [assets/output-template.md](assets/output-template.md).
3. **Blocked list** — each non-packageable engagement with its itemized reason(s).
4. **Machine-readable** — the packaging records keyed by `engagement_id` with `rubric_version`.
5. **Standing note** — "Draft third-party AI due-diligence package for human review only; this
   skill does not approve, onboard, or reject any provider, does not accept risk, and does not
   sign or execute any contract — every finding and the recommended disposition require human
   adjudication before any onboarding decision."

## Privacy and records
**Confidential.** Provider evidence may include NPI/PII, security detail, and commercially
sensitive material — apply data minimization; include only what evidences a domain. Retain the
draft package, the `rubric_version`, evidence citations, the residual-risk basis, and the
reviewer sign-off with the engagement; log every read and every package produced with the
analyst identity. Segregation of duties: the assessor drafts; a separate authority adjudicates.

## Gotchas
- **Drafting ≠ deciding.** The package is a draft; a human adjudicates. Never emit
  "approved/onboarded/rejected", "risk accepted", or "contract signed" language.
- **`do-not-proceed` is a recommendation, not a rejection.** It advises against onboarding on
  the current evidence; the accountable authority decides.
- **The rubric drives everything.** Required domains, evidence, freshness, and gates come from
  the versioned rubric; the wrong version produces the wrong package. Record `rubric_version`.
- **Every finding needs an evidence item.** A persuasive sentence with no backing exhibit is an
  unsupported finding and is stripped by the output screen.
- **Hard gates force Critical.** Unapproved data residency, no incident-notification right, no
  production exit plan, or unmanaged concentration force `Critical` / `do-not-proceed` — a
  strong signal for the adjudicator, never an autonomous block.
- **Evidence expires.** A SOC 2 or evaluation outside its window is `stale-evidence`; refresh
  it rather than packaging on an out-of-date artifact.
