# Changelog — investment-recommendation-evidence-reviewer

## 0.3.0 — 2026-10-04

- Add portable source-field review and exact-recipient draft gates for P5.
- Preserve existing calculation modes; distinguish native validation from separately reviewed source fidelity and audience scope.

## [0.2.1] — 2026-09-17

P4 live-model evaluation exposed unsupported evidence-reviewer/date attribution
copied from an applicability reviewer and packet date. Require field-level source
comparison and explicit nulls for missing evidence-specific review facts. An
executed regression confirms incomplete status and preserved nulls without
changing calculation/schema behavior. Preserve initial failures and report cold
follow-up runs separately in the P4 validation record.

## [0.2.0] — 2026-09-16
- Renamed from suitability-reg-bi-reviewer to identify the actual evidence-review job.
- Replaced implicit retail/institutional legal routing with a cited human-owned capacity,
  jurisdiction and retirement applicability profile; account recommendations need no fictitious security.
- Added fixed check/item inventories, source and subject linkage, reviewer/date coverage,
  policy-sourced disclosure timing, complete unresolved-item propagation and output recomputation.
- Removed Evidence-complete as a disposition; common statuses are needs-data and review-ready,
  both explicitly internal drafts requiring human review and making no legal/investment determination.
- Replaced v0.1 fixtures with a versioned contract and executable regressions for missing costs,
  conflicts and supervision, empty output, late disclosures, unknown citations and result tampering.
- Uses synchronized wealth-p0-v1 helper and deterministic full-input hashes; no connectors or actions.
- Added mandatory structured unresolved-issue lists, cited upstream artifact references and handoff
  mapping after independent scenario review. Explicit concerns prevent review-ready even when
  assessment says documented; regressions cover retained risk gaps and dropped-output issues.

### Pending before release
Domain SME, control owner and legal/compliance review of policy profiles and item coverage;
blind real-model trigger/task-quality/injection evaluations; source-system provenance and access
validation; bounded read-only integration testing and professional acceptance. Script tests are
software evidence only. No approval or regulatory certification is asserted by this changelog.

## [0.1.0] — 2026-07-17
Original suitability-reg-bi-reviewer prototype. The legacy schema and its unsafe completeness
mapping are superseded; old artifacts require source-backed migration and re-review.
