---
name: financial-document-version-comparator
description: >-
  Compare two versions of a financial document — term sheet, offering document, research draft,
  model, presentation, or policy/client version — and identify added, removed, and changed
  sections and changed data values with precise locations and citations, producing a
  source-linked change log for human review. Use when an investment-banking analyst,
  document-control analyst, or transaction manager asks to "diff these versions", "what changed
  between drafts", "compare the term sheets", or "find the redlines/data changes". HARD
  BOUNDARY: R2 read-only — it NEVER assesses legal significance or materiality, approves a
  document, determines disclosure sufficiency, or edits/publishes any version; it locates
  changes for a human reviewer.
license: MIT
compatibility: Amazon Quick Desktop; requires document-intelligence and controlled document-repository MCP integrations (read-only); bundled scripts are stdlib-only over structured document JSON.
metadata:
  aws-fsi-category: "Investment Banking & Research"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 5 - 2026 industry expansion"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (MNPI / client-confidential)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Investment Banking / Research"
  aws-fsi-primary-user: "Investment-banking analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Financial Document Version Comparator

## Purpose and outcome
Deterministically diff two structured versions of a financial document and produce a precise,
cited change log — added/removed/changed sections and changed data values, each located by
section id/heading and version. A successful output lets a human reviewer see exactly what
changed; the skill never judges legal significance, materiality, or disclosure sufficiency, and
never edits or approves a version.

## Use when
- "Diff/compare these two versions", "what changed between the drafts / term sheets".
- "Find the redlines and data changes with locations".

## Do not use
- The user wants a judgment on **legal significance, materiality, or disclosure sufficiency** →
  out of scope; a licensed/legal reviewer decides.
- **Approving/publishing** a version → not supported; a human/document-control acts.
- **Contract obligation extraction** → `contract-obligation-extractor`.
- **Communications-compliance review of research** → `communications-compliance-reviewer`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Emits a change log with a durable
`comparison_id`; it does not judge, edit, approve, or publish.

## Inputs and prerequisites
- Two versions as structured JSON: `doc_id`, `version`, and `sections` with `id`, `heading`,
  `text`, and optional `values` (named data fields). Schema:
  [scripts/validate_input.py](scripts/validate_input.py).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The controlled document repository is
authoritative for both versions; cite every change to a section id and both versions.

## Workflow
1. **Validate input** — run `validate_input`; confirm two versions of the same `doc_id`.
2. **Diff (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): section add/remove,
   normalized-text change, and per-field value change, each with location.
3. **Assemble the change log** — changes by type with before/after and citation.
4. **Validate output** — run [scripts/validate_output.py](scripts/validate_output.py) for change
   citation coverage, the no-significance/no-approval screen, and disclaimer.

## Validation loop
`validate_input` before, `validate_output` after. If a change lacks a location/citation, or the
text asserts materiality/approval/disclosure-sufficiency, **fix or fail closed**.

## Human approval
`external-delivery`: human review before external delivery. No version is ever edited, approved,
or published.

## Failure handling
- **Different `doc_id`s** → stop; the versions are not comparable; ask for the correct pair.
- **Missing section ids** → treat as add/remove by position only if ids are absent, and flag the
  ambiguity; never guess a mapping.
- **Binary/opaque content** → report "not comparable (unstructured)"; do not fabricate a diff.
- **Stale repository copy** → cite the version/as-of; flag. **Tool timeout** → partial + incomplete.

## Output contract
1. **Summary** — doc_id, version A → version B, counts by change type.
2. **Changes** — per change: type (added/removed/text_changed/value_changed), section id +
   heading, field (for values), before → after (or excerpt), citation.
3. **Not-comparable / data gaps.**
4. **Machine-readable** — changes + `comparison_id`.
5. **Standing disclaimer** — "Change-location evidence only; not a judgment of legal
   significance, materiality, or disclosure sufficiency, and not an approval. No version has
   been edited or published."
See [references/controls.md](references/controls.md).

## Privacy and records
MNPI / client-confidential. Honor information barriers; restrict to the deal/coverage team.
Retain the change log + citations. Log read + external-delivery approval. Never exfiltrate.

## Gotchas
- **A change is not a materiality judgment.** Report what changed and where; the reviewer judges
  significance.
- **Text normalization**: whitespace/case-only differences are not substantive; the diff
  normalizes before comparing so trivial formatting doesn't flood the log — but a real wording
  change is always reported.
- **Value vs text**: a number that moved is a `value_changed` (before→after), not buried in prose.
- **Section identity**: rely on stable section ids; if ids are missing, flag the mapping
  ambiguity rather than inventing correspondences.
