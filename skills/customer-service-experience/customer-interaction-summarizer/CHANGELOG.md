# Changelog — customer-interaction-summarizer

All notable changes to this skill package. Versions follow semver in `aws-fsi-version`.

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** informational, read-only recap of a single customer interaction (call, chat,
  email, thread) with source-linked key points, sentiment, commitments, disclosures, and
  open actions.
- **Triggers:** positive (summarize this call/chat, what did we promise, open actions);
  negative (next-best-action, advice) with routing to adjacent skills.
- **Controls:** R1; no advice / next-best-action (deterministic language screen), no
  determination (complaint upheld/rejected, compliance, vulnerability, eligibility/coverage,
  fraud/AML), no fact/commitment invention, no interaction merging, identifier masking;
  external-delivery human approval.
- **Tools/data:** read-only CCaaS transcript, CRM/case-management, complaint system,
  approved knowledge/product terms; durable `summary_id`.
- **Scripts:** `validate_input.py` (schema, single interaction, citable segments,
  data-quality warnings for inaudible/unmasked/missing-timestamp) and `validate_output.py`
  (citation coverage, sentiment enum, identifier masking, advice/determination screen,
  disclaimer presence).
- **Evaluations:** trigger/routing, golden normal + multi-interaction edge, deterministic
  script checks, no-advice/no-determination safety, prompt-injection, external-delivery
  authorization.
- **Handoffs:** downstream to `next-best-action-assistant`, `complaint-resolution-assistant`,
  `call-quality-compliance-reviewer`, `vulnerable-customer-support-assistant`,
  `service-recovery-assistant`, `knowledge-answer-composer`, and (gated actions)
  `omnichannel-case-orchestrator`.

### Pending before release
- Domain SME + control-owner blind review; accessibility review of the output format.
- Wire read-only MCP integrations (CCaaS transcript, CRM/case, complaint system) at
  deployment.
- With/without benchmark vs. no-skill baseline.
