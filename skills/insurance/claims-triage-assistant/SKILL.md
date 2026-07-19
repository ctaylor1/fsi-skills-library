---
name: claims-triage-assistant
description: >-
  Triage newly reported insurance claims (FNOL): classify each claim's severity/complexity and
  urgency/service level from explainable drivers, surface (never answer) coverage questions,
  recommend specialist routing, and assemble a DRAFT triage summary for human review. Use when
  a claims intake or claims-operations handler needs to work an FNOL queue, prioritize new
  claims, flag coverage questions, or decide which claims need a fraud, subrogation, coverage,
  catastrophe, litigation, or complex-file specialist. HARD BOUNDARY: R3 decision-support,
  draft-only. This skill NEVER determines coverage, sets or changes a reserve, approves, denies,
  pays, settles, assigns (in the system of record), or closes a claim, and never concludes fraud
  or liability. Severity, urgency, coverage questions, and routing are recommendations a claims
  supervisor / adjuster of record must adjudicate; the skill sends and files nothing.
license: MIT
compatibility: Amazon Quick Desktop; requires claims/case-management, policy-administration, underwriting-rules/product-terms, document-intelligence, actuarial/catastrophe-data, and producer-system MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Insurance"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Draft & package"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Insurance underwriting & claims"
  aws-fsi-primary-user: "Claims intake / claims operations"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Claims Triage Assistant

## Purpose and outcome
Take a queue of newly reported claims (first notice of loss) and make it workable: for each
claim, recommend a documented **severity/complexity** band and an **urgency/service-level**
band from explainable drivers, **surface** any coverage questions (never answer them),
recommend the right **specialist routing**, and assemble a **draft triage summary** from the
approved template. The outcome is a prioritized, review-ready triage packet — a claims
supervisor and adjuster of record still own the coverage decision, the reserve, the
assignment, the payment, and any filing. The skill recommends; humans adjudicate.

## Use when
- "Triage my FNOL queue / prioritize these new claims by severity and urgency."
- "Which of these claims needs a specialist (fraud, subrogation, coverage, CAT, complex)?"
- "What coverage questions should I flag on this claim before it's worked?"
- "Give me a draft triage summary for this new loss."

## Do not use
- **Deciding coverage** (is/ is not covered, whether an exclusion applies) → surface the
  question and route to `coverage-gap-analyzer`; a human/licensed professional decides.
- **Explaining policy wording** to a handler/insured → `policy-document-explainer`.
- **Deep claim-file review** (chronology, reserve support, decisions) → `claims-file-reviewer`.
- **Fraud investigation / SIU referral drafting** → `claims-fraud-referral-assistant` (triage
  concludes no fraud).
- **Subrogation/recovery screening** → `subrogation-opportunity-screener`.
- **Reserve analysis / setting** → `reserving-analysis-assistant` (human-owned).
- Any request to **approve, deny, pay, settle, assign, close, or file** a claim → refuse;
  route to the adjuster of record / claims supervisor.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Triage is deliberately separated from
adjudication, adjusting, coverage analysis, and payment (distinct entitlements, accountability,
and case states). This skill emits a durable `claim_id` triage package and routes to the named
specialist skills or human owners; it must not perform their work.

## Inputs and prerequisites
- The claim(s) with `claim_id`, `policy_id`, `product`, `claim_type`, loss/reported dates,
  policy period + status, estimated exposure, injury/fatality/litigation flags, party list,
  fraud indicators, subrogation potential, catastrophe code, exclusion hits, vulnerability
  flag, and a `source_ref`; the versioned **severity map** + **triage config** (thresholds,
  SLA targets). Schema and required fields: [scripts/validate_input.py](scripts/validate_input.py).
- Read access to claims/case-management, policy administration, underwriting rules/product
  terms, document intelligence, and actuarial/catastrophe data (all read-only). No value is
  fabricated: what is not supplied becomes a `needs-data` gap.

## Source hierarchy
See [references/source-map.md](references/source-map.md). Claims/case-management is the system
of record for claim state and `claim_id`; policy administration for period/status/coverages;
product terms for exclusions and effective-dated grants. Cite every asserted item as
`{system}:{ref}@{date/version}`. Coverage questions are assessed against the terms **in force
at the date of loss**. The severity map and triage config are **versioned contracts**.

## Workflow
1. **Validate & normalize** — run `validate_input`; surface data gaps (no exposure, missing
   injury/status, incomplete policy period) as warnings; flag what cannot be resolved.
2. **Classify (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): compute the
   documented severity and urgency bands from explainable drivers, surface coverage questions,
   and build routing recommendations. Rules: [references/domain-rules.md](references/domain-rules.md).
3. **Assemble the draft** — populate [assets/output-template.md](assets/output-template.md)
   into `draft_summary.body`: all six required sections, the DRAFT marker, the recommended
   bands, cited drivers, coverage questions, and routing.
4. **Fail closed where required** — an unmapped `claim_type` is `needs-data` (never guessed);
   a liability claim with undetermined liability is `needs-review` (human adjudication). The
   engine never manufactures a routing to fill a gap.
5. **Record approvals & hand off** — mark `human_adjudication_required`, record the pending
   `triage_lead_review` and `claims_supervisor_approval`, and route to the named specialist /
   human owner. Never decide, assign, pay, close, or send.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check enforces: allowed dispositions only; severity/urgency bands tie out to
their documented scores under the band cutoffs the engine recorded (`triage_config`), not
hardcoded thresholds; every draft carries all required template sections + the DRAFT marker
+ citations; required human approvals are recorded; no coverage/decision/reserve/fraud/
liability language (no unsupported assertions); no executed/send/assign/file/pay/close
language; standing note present. Fail closed on any miss.

## Human approval
`required`. Every triage output is a **recommendation for human review**. A claims triage lead
reviews the recommended bands, coverage questions, and routing, and a claims supervisor /
adjuster of record signs off before **any** queue/adjuster assignment, reserve, coverage
decision, payment, closure, or system-of-record change. This skill proposes and packages;
humans decide.

## Failure handling
- **Unmapped `claim_type`** → `needs-data`; state the missing severity mapping; do not guess a band.
- **Undetermined liability on a liability claim** → `needs-review`; route to human adjudication.
- **Incomplete policy period / missing status** → coverage screen limited; flag the gap; never
  assume cover was (or was not) in force.
- **Coverage question surfaced** → recommend `coverage-gap-analyzer`; the skill states the
  question, never the answer.
- **Tool timeout / unresolvable data** → return partial triage with an explicit incomplete
  flag; no retry assumption, no guessing.

## Output contract
See [references/controls.md](references/controls.md) and
[assets/output-template.md](assets/output-template.md).
1. **Draft triage summary** (per claim) — the six template sections (claim summary; severity
   and complexity; urgency and service level; coverage questions to resolve; recommended
   routing; human adjudication required), DRAFT-marked, with cited drivers.
2. **Machine-readable manifest** — per claim: `claim_id`, severity/urgency score + band + reason,
   coverage questions, routes, `disposition`
   (`draft-ready` | `refer-specialist` | `needs-data` | `needs-review`), citations, and the
   pending `triage_lead_review` / `claims_supervisor_approval` approvals.
3. **Queue summary** — counts by disposition.
4. **Standing note** — "Draft claims triage only … No coverage decision, reserve, payment,
   assignment, or claim closure has been made."

## Privacy and records
**Highly Confidential — customer NPI/PII.** Mask policy/claimant identifiers in output to what
evidences the triage; restrict draft outputs to the claims team. Retain triage records,
recommended bands, coverage questions, and citations with the severity-map/config versions
used; log the triager identity on every read and draft. Assess coverage questions against
effective-dated terms in force at the date of loss. Data stays within the deployment's
residency boundary.

## Gotchas
- **Triage ≠ coverage decision.** Surfacing a coverage question is not answering it. The skill
  never states a claim is or is not covered, or that an exclusion applies.
- **Severity is handling complexity, not a reserve.** The severity band ranks handling effort;
  it is not an exposure figure and never sets or implies a reserve.
- **Fraud indicators are a referral signal, not a finding.** Route to
  `claims-fraud-referral-assistant`; triage concludes no fraud.
- **Liability is a human adjudication.** A liability claim with undetermined liability is
  `needs-review`, never auto-routed as if liability were settled.
- **Recommend a queue; never assign it.** Assignment in the claims system, the reserve, the
  payment, and any filing are human-owned via the approval broker.
- **Versioned contracts.** Record the severity-map and triage-config versions on every triage
  record so the classification is reproducible and reviewable.
