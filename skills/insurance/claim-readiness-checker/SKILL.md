---
name: claim-readiness-checker
description: >-
  Check whether an insurance claim package is complete and ready to submit: inventory
  required documents, forms (signed, correct version), required fields, coverage-relevant
  evidence presence, chronology consistency, and notice/proof-of-loss/suit deadlines, then
  report present items, gaps, and a readiness status with cited evidence. Use when a
  policyholder or claims-intake specialist asks "is my claim complete", "what am I missing
  before I file", "check this claim file before the adjuster sees it", or needs a
  submission-readiness checklist. This skill checks completeness and timeliness and proposes
  a readiness status; it NEVER decides coverage or eligibility, adjudicates/approves/denies/
  settles/prices/pays a claim, determines an exclusion, or makes a fraud finding — those are
  human adjuster / insurer decisions.
license: MIT
compatibility: Amazon Quick Desktop; requires policy-administration, claims, document-intelligence, and approved-config MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Insurance"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 1 - stabilize existing"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "existing-updated"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Insurance underwriting & claims"
  aws-fsi-primary-user: "Policyholder / claims intake specialist"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Claim Readiness Checker

## Purpose and outcome
Given a claim package (policy metadata, claim fields, key dates, deadline schedule, and the
document/form manifest), run a set of **explainable readiness checks**, attach cited
evidence to each inspected item, list the **gaps** (missing documents/forms, incomplete
fields, chronology conflicts, near/passed deadlines), and produce a **readiness status**
(`Ready` / `Ready with minor gaps` / `Not ready`). A successful output lets a policyholder or
intake specialist submit a complete package, or lets an adjuster receive one — the coverage
decision, and any claim action, remains human.

## Use when
- "Is my claim complete and ready to submit, or am I missing anything?"
- "Check this claim file for missing documents, forms, and deadlines before the adjuster sees it."
- "Which required forms are unsigned or on the wrong version?"
- An intake specialist needs a consistent, cited completeness checklist to attach to a file.

## Do not use
- The user wants a **coverage/eligibility decision** ("is this covered", "does an exclusion
  apply", "am I eligible"), a **settlement/payout amount**, or the claim **approved/denied/
  paid** → out of scope; report readiness and route the decision to a human adjuster.
- **Adjuster-side file review** of an open claim (coverage evidence, chronology, disposition)
  → `claims-file-reviewer`.
- **Triage/assignment** of a submitted claim by severity/complexity/urgency →
  `claims-triage-assistant`.
- The claim was **denied** and the user wants an **appeal** → `claim-denial-appeal-helper`.
- **Coverage adequacy vs. exposure** (not file completeness) → `coverage-gap-analyzer`;
  plain **policy explanation** → `policy-document-explainer`.
- **Potential-fraud referral** → human-initiated `claims-fraud-referral-assistant` (this
  skill never makes a fraud finding).

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a readiness assessment
with a durable `readiness_id`; downstream triage/review/appeal skills consume it. It must not
duplicate their decision, disposition, or action steps.

## Inputs and prerequisites
- Claim identifier, policy number, `claim_type`, and `as_of` date.
- **Key dates** (policy period, date of loss, date reported, date prepared) and a **deadline
  schedule** (notice of loss, proof of loss, suit limitation) where available.
- **Document/form manifest** — each item with `type`, `status`
  (`present`/`missing`/`illegible`/`pending`), and for forms `signed` + `form_version`, plus
  a `source_ref` to cite. Schema: [scripts/validate_input.py](scripts/validate_input.py).
- Read access to policy administration, claims, and document intelligence; the versioned
  required-item / deadline config (see [references/domain-rules.md](references/domain-rules.md)).

## Source hierarchy
See [references/source-map.md](references/source-map.md). Policy administration is the
position of record for the policy period, endorsements, and the required-item/deadline
schedule; the claims system holds the claim and its manifest; document intelligence resolves
presence/legibility/signature/version. Cite every inspected item to a source; never infer
coverage from a document conflict.

## Workflow
1. **Scope & load** — confirm the claim, policy, and `claim_type`; load the manifest, dates,
   and deadline schedule for the config; validate with `validate_input`.
2. **Run checks (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to evaluate
   required documents, required forms (signed + accepted version), required fields,
   chronology consistency, and deadline timeliness. Each check returns cited evidence for the
   items it inspected and records gaps; checks it cannot run become `not_evaluable`.
3. **Classify gaps** — each gap is `blocking` (missing/invalid required item, missing field,
   chronology conflict, missed hard deadline) or non-blocking (recommended item, at-risk
   deadline).
4. **Map status** — map the gap profile to `Ready` / `Ready with minor gaps` / `Not ready`
   per the documented deterministic mapping. This is a completeness triage for a human,
   explicitly **not** a coverage or claim decision.
5. **Write the assessment** — plain-language summary + present items + gaps (with what to
   obtain) + deadline table + `not_evaluable` items + considerations + disclaimer.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check confirms: every inspected item's evidence is cited, every gap is
traceable, the status maps deterministically from the gaps, no coverage/eligibility/claim-
decision/fraud language is present, the standing disclaimer is included, and considerations
accompany any gap. Fail closed on any miss.

## Human approval
`external-delivery`: human review required before the assessment is sent to the
policyholder/producer or written to the claim system of record. No approval is needed for the
specialist's own read. The skill never takes a claim action.

## Failure handling
- **Missing policy dates / deadlines** → mark the affected checks `not_evaluable`; do not
  assume the claim is timely or in-period.
- **Ambiguous claim/policy identity** → stop and confirm; never assess the wrong claim.
- **Illegible / pending documents** → treat as not-present for readiness and say so; do not
  guess contents.
- **Stale/conflicting sources** (policy record vs. document) → cite both and flag; never
  resolve into a coverage inference.
- **Tool timeout** → return the checks completed so far with a clear "incomplete" flag.

## Output contract
1. **Summary** — claim (masked), policy, claim type, `as_of`, gap counts, readiness status.
2. **Checks** — per check: name, status, plain-language detail, and cited evidence for
   inspected items.
3. **Gaps** — per gap: item, category, blocking flag, what is missing/expiring, and what to
   obtain (factual, not advice).
4. **Deadlines** — per-deadline `days_remaining` table with citations.
5. **Not-evaluable checks** and their reason.
6. **Considerations** — reminders that readiness is not a coverage/claim decision.
7. **Machine-readable** — checks + gaps + `readiness_id` for downstream skills.
8. **Standing disclaimer** — "Readiness and completeness check only; not a coverage,
   eligibility, or claim decision. No claim has been adjudicated, approved, denied, or paid."
See [references/controls.md](references/controls.md).

## Privacy and records
Customer NPI/PII. Mask policy/claim identifiers where feasible (last 4). Minimize claimant
data in output to what evidences a gap or a present item. Retain the assessment + citations +
config version per records policy; log the read and any external-delivery approval. Never
exfiltrate claimant data.

## Gotchas
- **Readiness is not coverage.** A complete file can still be denied; an incomplete file can
  still be covered. Never let a `Ready` status read as a coverage or claim decision.
- **Present ≠ valid.** A form that is present but unsigned or on a superseded version is a
  gap; a required document marked `illegible` or `pending` is not "present".
- **Deadlines are surfaced, not set.** This check computes days remaining against `as_of`;
  the controlling legal deadline comes from the policy and jurisdiction — verify it there.
- **Chronology flags facts, not fault.** A loss dated outside the policy period is a
  chronology gap to reconcile, not a coverage conclusion.
- **Do not tune requirements to the claim.** Required-item sets, deadline dates, and
  thresholds come from the versioned config, not from what "should" be enough here.
- **Fraud language is off-limits.** Describe missing/inconsistent items factually; never
  assert or imply a claim is fraudulent — that is a separate human-led referral.
