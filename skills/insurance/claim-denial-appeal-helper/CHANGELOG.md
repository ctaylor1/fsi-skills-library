# Changelog — claim-denial-appeal-helper

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `existing-updated` relative to
the AWS baseline — stronger evidence-backing, deadline, and no-advice/no-determination
guardrails).

- **Scope:** explain denial reasons + map each to supporting evidence and policy provisions +
  flag gaps and the appeal deadline + draft a review-ready appeal package. Read-only; a human
  reviews and delivers. No coverage determination, no legal advice, no filing.
- **Domain rules (deterministic):** denial reason→evidence checklist (11 reason codes +
  generic fallback), argument points drafted only where cited evidence backs them, appeal
  deadline = denial_date + appeal_window_days with open/due_soon/past_due status, and a
  readiness map (ready_to_draft vs gaps_present). See `references/domain-rules.md` and
  `scripts/calculate_or_transform.py`.
- **Controls:** R2; hard boundary against legal advice, coverage/eligibility determination,
  guaranteed outcomes, filing on the member's behalf, and unsupported claims; versioned
  appeal-window/checklist config only; standing disclaimer required; `external-delivery`
  approval gate.
- **Scripts:** `validate_input` (denial-bundle schema, evaluability + deadline warnings),
  appeal work-product builder, `validate_output` (evidence-backing, deterministic
  deadline/readiness tie-out, prohibited-language screen, disclaimer, human-review gate, gap
  disclosure).
- **Assets:** `assets/output-template.md` appeal-package template (template fidelity; no
  uncited claims).
- **Evaluations:** trigger/routing, golden gaps-present case, closed-window edge, deterministic
  script checks, no-advice/no-determination safety + injection, external-delivery
  authorization.
- **Handoffs:** out to a licensed attorney (legal), `policy-document-explainer`,
  `coverage-gap-analyzer`, `policy-wording-comparator`; distinct from
  `claims-fraud-referral-assistant`, `claim-readiness-checker`, `claims-triage-assistant`.

### Pending before release
- Domain SME (claims appeals) + control-owner blind review; legal review of the no-advice /
  no-determination boundary and the standing disclaimer.
- Confirm the versioned appeal-window and reason→evidence checklist config source and owner,
  including jurisdiction/plan-level overrides.
- Wire read-only MCP integrations (denial notice/EOB, plan document, claims, document
  intelligence, config) at deployment.
