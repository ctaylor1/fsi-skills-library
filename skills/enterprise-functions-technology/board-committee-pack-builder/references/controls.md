# Controls — board-committee-pack-builder

- **Risk tier:** R2 — analytical / drafting support. **Action mode:** Draft-only; no
  system-of-record change.
- **Human approval:** `external-delivery` — a named human must review and approve before the
  pack is delivered to the committee or any figure is treated as decided. Internal drafting
  is reviewer-sampled.

## Prohibited (fail closed)

- **Sending, submitting, distributing, or finalizing** the pack (email, board portal,
  regulator, filing). The skill drafts; humans deliver.
- **Marking a decision approved / adopted / resolved** on its own, or presenting a proposed
  resolution as carried without a recorded human approver.
- **Unsupported assertions**: any decision, metric, risk, or issue without a resolvable
  citation to the approved-source register.
- **Fabricating or refreshing figures**: values come from cited sources with their `as_of`
  date; the skill does not invent, extrapolate, or silently update numbers.
- **Personalized investment / legal / tax advice**, or a binding regulated determination.

## Pack states (this skill may set only these)

The pack `status` is always `draft`. Individual decisions may be `proposed` (default) or
carry a human-supplied `approved`/`obtained` status **with** a recorded approver. The skill
may not set the pack to `final`, `issued`, `sent`, or `distributed`.

## Required output screens (`scripts/validate_output.py`)

- **Template fidelity:** cover, agenda, decisions, metrics, risks, issues, takeaways all
  present and non-empty; source register and approvals register present.
- **No unsupported claims:** `unsupported_claims` empty; every decision/metric/risk/issue
  carries at least one citation.
- **No unapproved claims:** a decision whose status is not a recognized non-decided state
  (`proposed`/`pending`/...) is treated as decided and must name a human approver; the check
  is an allowlist, so paraphrased or unrecognized decided-state wording fails closed.
- **Required approvals recorded:** every `requires_approval` decision appears in the
  approvals register with an approver_role and status.
- **Draft-only:** `status == "draft"`; no send/submit/distribute/finalize/board-approved
  language (regex screen).
- **Standing note present** (verbatim DRAFT banner).

## Segregation of duties

Pack drafting (this skill / corporate secretary) is separate from approving decisions
(committee members) and from delivering the pack (secretariat). The drafter does not
approve, and approval is not inferred from drafting.

## Data classification, privacy, records

- **Confidential.** Board material is need-to-know; distribute only via approved channels.
- Redact personal data not required for the decision; mask identifiers in supporting
  evidence to what the item needs.
- Retain the draft, the source register, and the approvals register with the
  `template_version`; log who assembled and who approved.
