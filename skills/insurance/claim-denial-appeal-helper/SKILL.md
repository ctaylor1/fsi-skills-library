---
name: claim-denial-appeal-helper
description: >-
  Explain why an insurance claim was denied, map each denial reason to the supporting evidence
  and governing policy provisions, flag the evidence gaps and the administrative appeal
  deadline, and draft a review-ready appeal package for the policyholder or claims advocate.
  Use when a member, advocate, or claims reviewer asks "why was my claim denied", "help me
  appeal this denial", "what evidence do I need to appeal", or needs an appeal letter and
  evidence index built from an EOB / denial notice. This skill provides administrative appeal
  support only: it NEVER gives legal advice, NEVER makes a coverage or eligibility
  determination, NEVER guarantees the appeal will succeed, and NEVER files or submits the
  appeal — those are the insurer's, an independent external reviewer's, or a licensed
  attorney's role.
license: MIT
compatibility: Amazon Quick Desktop; requires policy-administration, claims, underwriting-rules, document-intelligence, and approved-source-retrieval MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Insurance"
  aws-fsi-skill-type: "Guidance or domain-expertise skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Domain workflow"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 1 - stabilize existing"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "existing-updated"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Insurance underwriting & claims"
  aws-fsi-primary-user: "Policyholder / claims advocate"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Claim Denial Appeal Helper

## Purpose and outcome
Given a denied claim — a denial notice / EOB, the governing plan document, and any supporting
documents — explain each denial reason in plain language, map it to the **supporting evidence
and policy provisions**, report which evidence is present versus a **gap**, compute the
**administrative appeal deadline**, and draft a **review-ready appeal package**. A successful
output lets a policyholder or claims advocate understand the denial and assemble a
well-evidenced appeal. The coverage decision on the appeal stays with the insurer or an
independent external reviewer; legal questions go to a licensed attorney.

## Use when
- "Why was my claim denied — and how do I appeal it?"
- "Draft an appeal package / appeal letter for this EOB denial."
- "What evidence am I missing to appeal this denial?"
- "When is my appeal deadline?"
- A claims reviewer or advocate needs a consistent, cited appeal work-product to attach to a
  case.

## Do not use
- The user wants **legal advice**, a bad-faith/litigation assessment, or "should I sue?" →
  out of scope; refer to a **licensed attorney**.
- The user wants a **coverage or eligibility determination** ("is this covered — yes or no?")
  → that is the insurer's or external reviewer's decision. For plain-language policy
  understanding use `policy-document-explainer`; for coverage-gap analysis use
  `coverage-gap-analyzer`.
- The claim is **not yet submitted** (pre-denial completeness) → `claim-readiness-checker`.
- A **fraud referral** is needed → `claims-fraud-referral-assistant`.
- Insurer-side **claim intake/triage** → `claims-triage-assistant`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits an appeal package with
a durable `appeal_id`; a human reviews and delivers it. It must not file, decide coverage, or
give legal advice — those belong to the plan's appeal process, an external reviewer, or an
attorney.

## Inputs and prerequisites
- The **claim identifier** and the **denial notice / EOB** with its denial reason codes and
  denied lines.
- The **appeal window** stated on the notice (days) and the **appeal level** being pursued.
- The **plan/policy document** in effect on the date of service for the governing provisions.
- Any **supporting documents** already gathered (clinical notes, letters of medical
  necessity, corrected coding, proof of timely filing, primary EOB, etc.), each with a source
  reference. Schema: [scripts/validate_input.py](scripts/validate_input.py).
- Read access to policy-administration, claims, and document-intelligence; the versioned
  appeal-window and reason→evidence config (see [references/domain-rules.md](references/domain-rules.md)).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The **denial notice** governs what
was denied and why; the **plan document** governs the rules the appeal argues under. Cite
every reason to the notice line and every provision to the plan section. If the notice and
the plan text conflict, cite both and flag for the reviewer — never resolve silently.

## Workflow
1. **Scope & validate** — confirm the claim, denial reasons, appeal window, and appeal level;
   load supporting documents; run `validate_input`. Fail closed on structural gaps; note
   data-quality warnings (missing docs, a near/closed deadline, unmasked ids).
2. **Explain the denial** — restate each reason neutrally, citing the notice line and the
   governing plan provision. Do not judge whether the denial was correct.
3. **Map evidence (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to map each denial
   reason to its supporting-evidence checklist, match present evidence, list gaps, attach
   supporting policy refs, and draft an **argument scaffold only where cited evidence backs
   it**.
4. **Compute the deadline** — `appeal_deadline = denial_date + appeal_window_days`, with
   `days_remaining` and a `deadline_status` (open / due_soon / past_due). This is arithmetic
   on stated dates, not a legal opinion on late-appeal acceptance.
5. **Assemble the package** — plain-language explanation per reason + cited evidence + drafted
   argument points + outstanding-evidence list + deadline, following
   [assets/output-template.md](assets/output-template.md). Mark it for required human review.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check confirms: every drafted argument point is evidence-backed and cited;
no legal-advice / coverage-determination / guaranteed-outcome / filed-on-behalf language is
present; the deadline and readiness match the deterministic computation; the standing
disclaimer is present; the draft is marked `human_review_required`; and evidence gaps are
disclosed. Fail closed on any miss.

## Human approval
`external-delivery`: human review is required before the package is delivered to the member /
advocate or sent to the plan. No approval is needed for the reviewer's own read. The skill
never files, submits, or transmits the appeal.

## Failure handling
- **Missing denial reason / notice** → stop and request it; do not guess why the claim was
  denied.
- **Unknown reason code** → use the generic evidence checklist, flag it, and ask for the
  specific basis.
- **No supporting documents** → report every checklist item as a gap; draft no argument
  points; state readiness `gaps_present`.
- **Closed / near appeal window** → flag the deadline prominently; do not imply a late appeal
  will still be accepted; route the timeliness question to the plan or an attorney.
- **Notice vs. plan conflict** → cite both and flag; do not resolve.
- **Ambiguous claim/member identity** → stop and confirm; never build the package on the
  wrong claim.
- **Tool timeout** → return the reasons mapped so far with a clear "incomplete" flag.

## Output contract
1. **Summary** — claim (masked), denial date, appeal level, deadline + days remaining +
   status, evidence readiness, `appeal_id`.
2. **Per denial reason** — plain-language explanation (cited to the notice line + plan
   provision), evidence present (cited), evidence gaps, and drafted argument points (only
   where evidence backs them).
3. **Outstanding evidence** — what to gather before submission.
4. **Next steps** — administrative only; human review required before delivery.
5. **Machine-readable** — the appeal work-product + `appeal_id` for reuse.
6. **Standing disclaimer** — "Administrative appeal support only; not legal advice and not a
   coverage determination. The insurer or an independent external reviewer decides the appeal;
   no appeal has been filed on the member's behalf."
See [references/controls.md](references/controls.md).

## Privacy and records
Customer NPI/PII and PHI. Mask member/claim identifiers to the last 4. Minimize clinical
detail to what evidences an argument. Retain the appeal work-product + citations + config
version per records policy; log the read and the external-delivery approval. Never exfiltrate
member or clinical data.

## Gotchas
- **Support is not a determination.** A strong evidence map argues the member's case; it never
  concludes the claim *is* covered or the denial *is* invalid — that is the insurer's or
  external reviewer's call.
- **No argument without evidence.** If the supporting document is not in the bundle, it is a
  gap, not an assertion. The output template and `validate_output` both enforce this.
- **The deadline is on the notice.** Appeal windows vary by plan, jurisdiction, and appeal
  level; use the value stated on the denial notice, not a default assumption.
- **Use the plan version in effect on the service date**, which may differ from the current
  plan document.
- **Legal-sounding words are a trap.** "Bad faith", "legally entitled", "guaranteed", and
  "we filed" are prohibited — the skill supports an administrative appeal; it does not advise,
  determine, guarantee, or file.
- **PHI minimization.** Attach clinical documents as cited evidence; do not restate sensitive
  diagnoses beyond what the argument needs.
