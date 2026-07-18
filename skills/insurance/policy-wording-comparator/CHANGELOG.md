# Changelog — policy-wording-comparator

## [0.1.0] — 2026-07-18
Initial authoring in the FSI Skills Library (baseline status: `new`). R3 read-only
decision-support: cited wording findings + reviewer questions, mandatory human adjudication, no
autonomous regulated decision.

- **Scope:** clause-level comparison of a subject form/endorsement/edition against an approved or
  filed baseline form — added / removed / modified clauses, dangling-reference conflicts, and
  missing-required-clause gaps — each with both-side citations and a neutral reviewer question.
- **Findings (deterministic):** alignment by `clause_id`; materiality by clause type or `difflib`
  text-change ratio; escalation on escalation clause types (insuring agreement, exclusion, limit,
  coverage trigger, condition precedent), filed-form deviation, conflicts, or gaps (see
  `scripts/calculate_or_transform.py` and `references/domain-rules.md`).
- **Review track (deterministic):** No material changes / Standard review / Legal-compliance review
  required — a triage suggestion for a human, never a coverage, compliance, or filing decision.
- **Controls:** R3; hard boundary against coverage/compliance determinations, form approval, filing,
  binding, and review closure; versioned-config materiality only; `required` human approval.
- **Scripts:** `validate_input` (form/clause schema, evaluability warnings), comparison engine,
  `validate_output` (both-side evidence/citation completeness, deterministic track tie-out,
  escalate⊆material consistency, decision/filing/coverage/closure language screen, legal-handoff
  presence, standing disclaimer).
- **Evaluations:** trigger/routing, golden Legal-compliance-review case, baseline-not-of-record
  edge, deterministic script checks, no-decision safety + injection, adjudication-required
  authorization.
- **Handoffs:** downstream to `policy-document-explainer`, `coverage-gap-analyzer`,
  `policy-renewal-reviewer`, `reinsurance-treaty-interpreter`, `premium-quote-comparator`; upstream
  from `underwriting-workbench-assistant`, `submission-intake-triager`, `policy-renewal-reviewer`;
  filing/approval/coverage adjudication reserved for licensed humans and authorized systems.

### Pending before release
- Domain SME (product counsel) + control-owner blind review; legal/compliance sign-off of the
  materiality taxonomy and escalation rules.
- Confirm the versioned materiality/required-clause config source and its owner.
- Wire read-only MCP integrations (filed/approved forms, form repository, document-intelligence,
  product-rules config) at deployment.
