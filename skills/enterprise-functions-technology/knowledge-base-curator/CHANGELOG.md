# Changelog — knowledge-base-curator

## [0.1.0] — 2026-07-18
Initial authoring in the FSI Skills Library (baseline status: `new`). Created to give
knowledge managers a controlled, source-mapped way to find stale, duplicate, conflicting,
missing, and ownerless knowledge and to DRAFT the fixes — without ever touching the KB
itself.

- **Scope:** classify each article (`conflicting` / `retire` / `duplicate` / `stale` /
  `ownerless` / `current`) by documented precedence, detect `missing` required-topic gaps,
  and draft per-finding proposals with a human-approval register. Draft-only; no
  system-of-record change.
- **Controls:** R2; `external-delivery` approval; never publish/edit/merge/retire/delete;
  no done-state on a finding; every finding cites the KB record and/or an approved
  source-of-truth; the source-of-truth outranks the article; versioned thresholds and
  required-topic registry.
- **Scripts:** `validate_input` (KB-export schema, source-register resolution, data-gap
  warnings), `calculate_or_transform` (deterministic classification + severity + proposals +
  approvals + unsupported-claim detection), `validate_output` (draft-only status, template
  fidelity, no unsupported claims, approvals recorded, no delivery/change language, standing
  note).
- **Assets:** `assets/output-template.md` — the DRAFT curation-worklist template whose
  required sections the output validator enforces.
- **Evaluations:** trigger/routing, a golden 7-article + 1-missing-topic export exercising
  every finding branch, deterministic script checks, and a non-compliant output fixture that
  must fail closed (safety), plus injection / unsupported-claim / no-apply refusals.
- **Handoffs:** downstream to `policy-document-assistant`, `knowledge-answer-composer`,
  `policy-procedure-gap-analyzer`, `regulatory-change-impact-analyzer`; applying,
  publishing, merging, and retiring are human/operations actions (content owner,
  records/retention owner, knowledge governance).

### Pending before release
- Knowledge-governance control-owner + records/retention review; segregation-of-duty review.
- Confirm the curation config (staleness thresholds, high-risk tags), required-topic
  registry, and approved source-of-truth register — their source, owner, and versioning.
- Wire read-only MCP integrations (KB/CMS, controlled-content library, source-of-truth
  retrieval) at deployment.
