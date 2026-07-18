# Changelog — financial-statement-audit-assistant

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). Created to draft and
package audit **support** working papers — tie-outs, sampling, testing evidence, misstatement
accumulation, and issue tracking — while keeping the audit opinion and every conclusion a
human judgment.

- **Scope:** map financial-statement captions to the trial balance and tie them out, build a
  documented monetary-unit sample, record cited findings, accumulate misstatements against
  materiality, and assemble the eight-section working-paper draft. Draft-only; no
  system-of-record change.
- **Controls:** R2; no audit opinion / conclusion on fair presentation, materiality, or going
  concern; no ICFR/SOX effectiveness opinion; no deliver/file/submit; no manufactured
  sign-off; every tie-out and finding cited; versioned planning parameters.
- **Scripts:** `validate_input` (audit-request schema, needs-data warnings), the working-paper
  engine `calculate_or_transform` (tie-outs + MUS sampling + misstatement accumulation +
  section assembly), and `validate_output` (template fidelity, unsupported-assertion screen,
  audit-opinion/assurance language screen, draft-only screen, tie-out arithmetic, recorded
  approvals, standing note). Each runs `--selftest` on a bundled fixture.
- **Assets:** `assets/output-template.md` — the controlled eight-section working-paper draft
  with the verbatim standing note.
- **Evaluations:** trigger/routing, a golden audit request exercising ties, a flagged
  difference, MUS sampling with key items, finding de-duplication, and below-materiality
  accumulation; deterministic script checks; a non-compliant output that must fail closed;
  opinion- and delivery-refusal safety checks; a sign-off authorization refusal.
- **Handoffs:** upstream `month-end-close-orchestrator`, `gl-reconciler`,
  `financials-normalizer`; downstream/parallel `audit-evidence-packager`,
  `fpa-variance-analyzer`, `valuation-reviewer`, `regulatory-reporting-data-validator`,
  `management-reporting-packager`; opinion and delivery approval are human (engagement partner).

### Pending before release
- Engagement-partner + methodology (audit-documentation) review; segregation-of-duties review
  of preparer/reviewer/partner roles.
- Confirm the planning-parameter source (materiality, tolerable misstatement, reliability
  factor, sampling config), its owner, and versioning contract.
- Wire read-only MCP integrations (ERP/GL, subledgers, consolidation/FS package, FP&A,
  regulatory reporting, documents) at deployment.
