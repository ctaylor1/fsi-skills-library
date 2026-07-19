---
name: underwriting-workbench-assistant
description: >-
  Compile entity, property, exposure, loss, catastrophe, financial, and third-party risk
  information into a cited, underwriter-ready risk profile: assess data completeness and
  source freshness, apply the approved underwriting rule set, surface missing information and
  exceptions, and draft decision rationale for a human underwriter. Use when an underwriter or
  underwriting manager needs to assemble a submission's risk picture, check it against
  appetite and binding-authority rules, flag referrals and data gaps, or prepare draft
  rationale ahead of an accept/quote/decline decision. HARD BOUNDARY: draft-only decision
  support — it NEVER binds, quotes, declines, or issues coverage, NEVER makes an autonomous
  underwriting decision, and NEVER writes a system of record; every assertion is cited and the
  accept/quote/decline/bind decision stays with a licensed human underwriter.
license: MIT
compatibility: Amazon Quick Desktop; requires policy-administration, loss/claims-history, property/exposure, catastrophe-model, financial-data, third-party-risk-screening, and underwriting-rules/appetite/authority MCP integrations (all read-only).
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
  aws-fsi-primary-user: "Underwriter / underwriting manager"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Underwriting Workbench Assistant

## Purpose and outcome
Give an underwriter a single, cited, decision-support workbench for a submission. The skill
pulls entity, property, exposure, loss, catastrophe, financial, and third-party risk
information into one **underwriter-ready risk profile**, checks completeness and source
freshness, applies the approved underwriting rules (appetite, binding authority, capacity,
loss experience, catastrophe accumulation, third-party risk, financial strength), surfaces
findings and data gaps, and drafts a **decision rationale**. The outcome is a packaged draft
the underwriter reviews and acts on — the accept/quote/decline/bind decision, and any
policy-administration write, stay with the licensed human underwriter.

## Use when
- "Compile an underwriter-ready risk profile for this submission."
- "Pull loss, catastrophe, and third-party data together and flag underwriting exceptions."
- "What's missing or stale before I can underwrite this account?"
- "Draft the decision rationale / referral write-up for the underwriter."

## Do not use
- **Submission ingestion / extraction** (broker emails, ACORD forms, PDFs) →
  `submission-intake-triager`.
- **Coverage adequacy vs. needs** → `coverage-gap-analyzer`; **renewal comparison** →
  `policy-renewal-reviewer`.
- **Catastrophe accumulation analysis** → `catastrophe-exposure-monitor`; **treaty/facultative
  capacity** → `reinsurance-treaty-interpreter`; **form/wording checks** →
  `policy-wording-comparator`; **reserve/loss-development** → `reserving-analysis-assistant`.
- Any request to **bind, quote, decline, issue, or write policy administration** → refuse; the
  decision is the human underwriter's.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Upstream, `submission-intake-triager`
feeds normalized submission/exposure data. This skill emits a durable `workbench_id` + profile
and routes catastrophe, capacity, wording, and reserving questions to their owning skills;
adverse third-party flags go to the referral authority / financial-crime specialist as a human
handoff. The underwriting decision is always a human handoff, never performed here.

## Inputs and prerequisites
- A submission batch: `config_version`, review `as_of_date`, `authority` (binding-authority
  TIV/limit, appetite classes), and `submissions[]` each with `submission_id`, occupancy
  class, TIV, requested limit, and the seven `risk_sections` (entity, property, exposure,
  loss_history, catastrophe, financial, third_party), each carrying `source_ref` + `as_of`.
  Schema: [scripts/validate_input.py](scripts/validate_input.py).
- Read access to policy administration, loss/claims, property/exposure, catastrophe model,
  financial, and third-party-risk sources, plus the versioned rules/appetite/authority config.

## Source hierarchy
See [references/source-map.md](references/source-map.md). Policy administration is the system
of record for the submission (never written back here); the approved rules, appetite, and
authority config are versioned contracts. Cite every profile line item as
`{system}:{ref}@{date/version}`; age is measured against the review `as_of_date`, never the
system clock, so results are reproducible.

## Workflow
1. **Validate** — run `validate_input`; fail closed on structural problems; note gaps that
   force `needs-data`.
2. **Compile (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): assess completeness,
   check freshness vs. per-section SLAs, apply the approved rules, and assemble the profile.
3. **Classify disposition (advisory)** — missing/stale-critical data → `needs-data`; any rule
   finding → `refer-to-underwriter` (with routes); otherwise
   `ready-for-underwriter-review`. See [references/domain-rules.md](references/domain-rules.md).
4. **Draft rationale** — a recommendation framed "for underwriter adjudication", listing
   applied rule IDs, routes, and citations, with an empty `unsupported_claims`.
5. **Package** — fill [assets/output-template.md](assets/output-template.md); leave
   `human_adjudication` pending with `decision: null`.
6. **Never decide** — no bind/quote/decline/issue and no system-of-record write.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py) after.
The output screen enforces: only the three advisory dispositions; evidence-backed findings; no
unsupported claims; a pending `human_adjudication` (no autonomous decision); every required
output-template section present; no binding/decision/filing/system-of-record language; standing
note present. Fail closed on any miss.

## Human approval
`required`. This skill proposes and packages a draft; every referral disposition, and every
accept/quote/decline/bind and policy-administration write, needs a licensed human underwriter
(referrals to a senior underwriter / referral authority per delegated authority). See
[references/controls.md](references/controls.md).

## Failure handling
- **Missing / stale-critical data** → `needs-data`; list exactly what to obtain; never guess to
  complete a profile.
- **Ambiguous appetite/authority** → treat as a referral for human judgment, not an auto-pass.
- **Adverse third-party flag** → raise a referral and route to the referral authority; do not
  adjudicate sanctions/fraud here.
- **Stale/conflicting sources** → cite both, flag freshness, and refer.
- **Tool timeout / partial data** → return the partial profile with an explicit incomplete flag
  and `needs-data`; no retry assumption.

## Output contract
1. **Workbench view** — per submission: `workbench_id`, recommended disposition
   (`needs-data` | `refer-to-underwriter` | `ready-for-underwriter-review`), and a one-line
   cited reason.
2. **Risk profile** — completeness map, source-freshness table, rule findings (severity,
   message, evidence, route), all cited and masked.
3. **Draft decision rationale** — recommendation for underwriter adjudication, applied rule
   IDs, routes, citations; `unsupported_claims` empty.
4. **Human adjudication block** — pending, with the required approver and a null decision.
5. **Machine-readable** — the profiles keyed by `workbench_id` (see
   [assets/output-template.md](assets/output-template.md)).
6. **Standing note** — "Draft underwriting risk profile and decision support only; no coverage
   has been bound, quoted, declined, or issued, and no system of record has been updated."

## Privacy and records
**Highly Confidential (customer NPI/PII).** Mask insured identifiers to what the profile
requires. Retain the compiled profile, citations, applied rule IDs, and `config_version` for
underwriting-file recordkeeping and audit; log the compiling identity and the underwriter of
record. No external delivery from this skill.

## Gotchas
- **Compiling ≠ deciding.** The profile and disposition are decision support; the underwriter
  makes the accept/quote/decline/bind call. Never phrase a recommendation as a decision.
- **Cite or drop.** Any assertion without a source is a defect — list it as a gap, do not
  assert it. The output screen rejects unsupported claims.
- **Freshness is measured to the `as_of_date`.** A stale catastrophe or property source forces
  `needs-data`; do not underwrite on stale critical data.
- **Rules route, they don't rule.** A rule finding raises a referral for a human; it never
  auto-approves or auto-declines.
- **Config is versioned.** Record `config_version` on every profile so the rule application is
  reproducible and reviewable.
