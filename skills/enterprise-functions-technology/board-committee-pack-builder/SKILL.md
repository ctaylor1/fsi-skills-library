---
name: board-committee-pack-builder
description: >-
  Assemble a controlled board or committee pack: organize decisions and resolutions
  requiring approval, a KPI/metrics dashboard, risks, issues and matters arising, an
  approved-source register, an approvals register, and concise per-page takeaways into a
  template-faithful DRAFT with every claim mapped to an approved source. Use when a
  corporate secretary, executive office, or risk team needs to build or refresh a board /
  audit / risk-committee pack, tie report content back to authoritative sources, record
  which decisions need which approvals, and produce an audit-ready draft for human review.
  This skill is DRAFT-ONLY: it never sends, submits, distributes, or finalizes a pack, never
  marks a decision approved or a resolution adopted on its own, and never presents any claim
  without a resolvable approved-source citation — external delivery and every approval stay
  with the named humans.
license: MIT
compatibility: Amazon Quick Desktop; requires controlled-content/templates, management-reporting, risk-register/KRI, project/action-tracking, documents/contracts/procurement, and email/calendar MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Enterprise Functions & Technology"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Draft & package"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 2 - analytical production"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Confidential"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Enterprise Functions & Technology"
  aws-fsi-primary-user: "Corporate secretary / executive office / risk"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Board / Committee Pack Builder

## Purpose and outcome
Assemble a **controlled, template-faithful board or committee pack** from content produced
by other skills and people: decisions and resolutions, a metrics/KPI dashboard, risks,
issues and matters arising, the approved-source register, an approvals register, and concise
per-page takeaways. Every substantive line is mapped to an approved source and every
decision that needs approval is recorded with its approver and status. The outcome is an
**audit-ready DRAFT** the corporate secretary can review and route — not a delivered or
decided pack. Delivery and approval remain human steps.

## Use when
- "Build the Audit Committee pack for the August meeting."
- "Refresh the board pack with this quarter's metrics and risks and tie every figure to its
  source."
- "Which decisions in this pack need approval, and are the approvals recorded?"
- "Assemble the risk-committee pack draft with page takeaways for review."

## Do not use
- **Computing the numbers, rating the risks, or drafting the policies** in the pack — those
  are upstream skills (see Adjacent-skill handoffs); this skill cites them.
- **Tracking post-meeting actions / minutes** → `meeting-action-tracker`.
- **Sending, submitting, distributing, or finalizing** the pack, or **approving** any
  decision → human secretariat / committee. Refuse and route.
- **Personalized investment, legal, or tax advice**, or any binding regulated
  determination.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Content flows **in** from
`management-reporting-packager`, `enterprise-risk-assessment-builder`,
`key-risk-indicator-monitor`, `regulatory-change-impact-analyzer`,
`investment-committee-memo-builder`, `policy-document-assistant`, and
`enterprise-meeting-preparer` (each cited); the approved pack flows **out** to
`meeting-action-tracker` after the meeting. Approval and delivery are **human** steps this
skill records but never performs.

## Inputs and prerequisites
- A pack request: `pack_id`, committee, meeting date, `template_version`, classification, the
  **approved-source register** (`sources[]` with `as_of` dates), and the content sections
  (agenda, decisions, metrics, risks, issues, takeaways) with `source_ids`. Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Read access to controlled content/templates, management reporting, risk register/KRI,
  action tracking, and supporting documents.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The controlled content library
(template + minutes) ranks highest, then reporting, risk, and action systems. Cite every
substantive line as `{system}:{ref}@{as_of}`. The `template_version` is a versioned
contract; conflicting figures are shown side by side with both citations, never silently
reconciled.

## Workflow
1. **Validate the request** — run `validate_input`; confirm the source register, unique
   content ids, and that each content item's `source_ids` resolve. Warn on missing sections
   and unsourced items.
2. **Assemble deterministically** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): resolve each
   claim's citation, build the approvals register from `requires_approval` decisions, compute
   completeness, and collect `unsupported_claims`.
3. **Populate the template** — lay the assembled sections into
   [assets/output-template.md](assets/output-template.md) (cover, agenda, decisions,
   metrics, risks, issues, sources, approvals, takeaways).
4. **Record approvals, do not grant them** — decisions default to `proposed`; an `approved`
   status is carried through only when a named human approver is recorded.
5. **Validate the pack** — run `validate_output`; fix any template-fidelity, unsupported-
   claim, unapproved-claim, missing-approval, or draft-only failure. Fail closed.
6. **Hand to a human** — present the DRAFT for review, approval, and delivery. Never send.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check enforces: all required sections present; `unsupported_claims` empty
and every content item cited; every `requires_approval` decision recorded in the approvals
register; no decision presented as decided — any status other than a recognized non-decided
state such as `proposed`/`pending` — without a named human approver (allowlist, fails closed
on paraphrased wording); `status` is `draft` with no send/submit/distribute/finalize
language; standing DRAFT note present.
Fail closed on any miss.

## Human approval
`external-delivery`. A named human must review and approve the pack before it is delivered
to the committee and before any decision is treated as taken. This skill drafts and records
the approval **requirement and status**; it never approves a decision or delivers the pack.

## Failure handling
- **Unresolvable source** → list the item under `unsupported_claims`; do not present the
  claim as supported and do not invent a citation.
- **Missing required section** → mark it missing in `completeness`; the pack fails output
  validation until the section is provided.
- **Decision marked approved without an approver** → fail closed; keep it `proposed` and
  flag that a human approval must be recorded.
- **Conflicting figures across sources** → show both with citations; route to the content
  owner; do not pick a winner.
- **Stale source** → cite it with its `as_of` date; flag for refresh; never silently update.
- **Tool timeout / partial content** → return the partial pack with an explicit incomplete
  flag; no retry assumption.

## Output contract
1. **Assembled pack (DRAFT)** — cover, agenda, decisions (with approval routing), metrics,
   risks, issues, sources, approvals, and page takeaways, per
   [assets/output-template.md](assets/output-template.md).
2. **Source map** — every claim tied to its `{system}:{ref}@{as_of}` citation.
3. **Approvals register** — each `requires_approval` decision with approver role, approver,
   status, and date.
4. **Completeness report** — required sections present vs. missing.
5. **Unsupported claims** — must be empty for a passing pack.
6. **Machine-readable** — the full assembled-pack JSON keyed by `pack_id`.
7. **Standing note** — "DRAFT board/committee pack assembled for human review; nothing has
   been sent, submitted, distributed, or finalized, and no decision has been approved by
   this skill."
See [references/controls.md](references/controls.md).

## Privacy and records
**Confidential.** Board material is need-to-know; distribute only via approved channels
(a human step). Redact personal data not required for a decision and mask identifiers in
supporting evidence to what the item needs. Retain the draft, source register, approvals
register, and `template_version`; log who assembled and who approved. See
[references/controls.md](references/controls.md).

## Gotchas
- **Recording an approval is not granting one.** The approvals register captures who must
  approve and the current status; the skill never flips a decision to approved.
- **A takeaway is a summary, not a new claim.** Page takeaways condense already-cited
  content; they must not introduce an unsourced assertion.
- **Cite the date, don't refresh the number.** A stale figure is shown with its `as_of`
  date and flagged, never quietly updated to look current.
- **Draft-only means draft-only.** No board portal upload, email, or filing — assembling the
  pack and delivering it are different jobs with different owners.
- **The template is a contract.** Assemble against the approved `template_version` and record
  it; a missing required section blocks the pack rather than being dropped.
