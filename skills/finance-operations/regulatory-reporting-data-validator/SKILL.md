---
name: regulatory-reporting-data-validator
description: >-
  Validate a regulatory-reporting package before human sign-off: check input completeness,
  transformation/edit-check consistency, source reconciliations and tie-outs, period-over-period
  variance, timeliness against the due date, and preparer/reviewer/approver sign-off evidence
  (including segregation of duties), producing cited findings and a deterministic filing-readiness
  band. Use when a regulatory-reporting or finance-control user asks "validate this Call Report /
  FR Y-9C / FR 2052a / COREP package", "do the numbers tie to the GL", "is this report complete and
  on time", "check the sign-off evidence", or needs a review-ready exception list before filing.
  HARD BOUNDARY: this skill surfaces and evidences exceptions and a readiness band only; it NEVER
  certifies or attests accuracy, approves a report for filing, signs off, submits/files to a
  regulator, or posts GL corrections — those remain human/authorized-system actions.
license: MIT
compatibility: Amazon Quick Desktop; requires ERP/GL, subledger, consolidation, FP&A, regulatory-reporting, and document/spreadsheet MCP integrations plus approved threshold config (all read-only).
metadata:
  aws-fsi-category: "Finance & Operations"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 2 - analytical production"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Confidential (financial records)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Finance & Controllership"
  aws-fsi-primary-user: "Regulatory reporting / finance control"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Regulatory Reporting Data Validator

## Purpose and outcome
Given a regulatory-report package (report metadata, reported cells with lineage, declared
edit-check relationships, source reconciliations, an optional prior period, and sign-off
evidence), run a set of **deterministic, explainable validation checks**, attach cited
evidence to every exception, and produce a **filing-readiness band** (`Blocked` / `Review` /
`Clear`). A successful output gives the preparer and approver a review-ready exception list
and the specific evidence behind each item — so a human can remediate and decide. The
**filing decision, certification, sign-off, and submission remain human/authorized-system
actions**; this skill never makes or communicates them.

## Use when
- "Validate this Call Report / FR Y-9C / FR 2052a / COREP/FINREP package before we file."
- "Do the reported numbers tie back to the general ledger / subledger?"
- "Is the report complete — are all mandatory cells populated with lineage?"
- "Do the internal edit checks (subtotals, cross-foots) foot?"
- "Is the sign-off evidence there, and is segregation of duties satisfied?"
- "Are we on time relative to the due date, and what changed materially vs. last period?"

## Do not use
- The user wants the report **certified, approved for filing, signed off, or submitted** →
  out of scope. Surface exceptions + evidence and route to the human preparer/approver and
  the authorized filing system.
- **Posting GL/journal corrections** for a reconciliation break → `gl-reconciler` proposes
  corrections for approval; this skill only flags the break.
- **Transaction-level** regulatory reporting (trade/transaction reports: completeness,
  identifiers, field mappings, timeliness) → `transaction-reporting-quality-checker`.
- **Assembling** the management/regulatory narrative package after validation →
  `management-reporting-packager`; **audit evidence** with chain of custody →
  `audit-evidence-packager`; **audit tie-out/testing** support →
  `financial-statement-audit-assistant`.
- Normalizing inconsistent source statements into model-ready data →
  `financials-normalizer` (an upstream data-prep step).

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a validation findings
pack with a durable `validation_id`; downstream packaging/audit/exam skills consume it. It
must not duplicate their assembly, correction, sign-off, or filing steps.

## Inputs and prerequisites
- **Report metadata**: `report_code`, `period_end`, `as_of`, `due_date`, `jurisdiction`,
  `config_version`.
- **Reported cells**: each with `cell_id`, `value`, and `source_refs[]` (lineage to GL /
  subledger / prior filing).
- **Declared edit checks** (arithmetic relationships, e.g., subtotal = sum of components) and
  **reconciliations** (reported value vs. an authoritative source value with a tolerance).
- **Prior period** (optional) for period-over-period variance review.
- **Sign-off evidence**: preparer / reviewer / approver entries with `signed_at`.
- Approved, versioned **thresholds/config** (see [references/domain-rules.md](references/domain-rules.md)).
- Schema and structural rules: [scripts/validate_input.py](scripts/validate_input.py).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The ERP/GL (and its subledgers /
consolidation) is the position of record for balances; the regulatory instructions define
the cells, edit checks, and due dates; the versioned config supplies thresholds and required
roles. Cite every exception to a specific cell, reconciliation, edit check, or sign-off row.
Where a reported value and the GL conflict, cite both and flag the break — never resolve
silently.

## Workflow
1. **Scope & load** — confirm the report, period, and due date; load the package; validate
   structure with `validate_input`. Record the `config_version`.
2. **Run checks (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to evaluate:
   completeness, lineage, edit-checks/internal-consistency, reconciliation tie-outs,
   range/sign bounds, sign-off completeness, segregation of duties, timeliness, and
   variance-vs-prior. Each check returns a status, a plain-language reason, and the evidence
   rows behind it. Checks are **explainable**, not a black-box pass/fail.
3. **Assemble evidence** — for each fired finding, attach the specific cells/recons/edit
   checks/sign-offs and the basis (threshold, tolerance, expected value) with citations.
4. **Map readiness (deterministic)** — map the fired-findings profile to a readiness band
   per the documented mapping: any **blocking** finding → `Blocked`; only **advisory**
   findings → `Review`; none → `Clear`. This is a triage state for a human, explicitly
   **not** a filing determination.
5. **Write the pack** — plain-language finding-by-finding explanation + cited evidence + the
   readiness band + remediation next-steps + explicit data gaps / not-evaluable checks.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check confirms: every fired finding has ≥1 cited evidence row, the
readiness band equals the deterministic mapping from the findings, no
certification/approval/filing/submission language is present, the standing disclaimer is
present, and remediation prompts are included when any finding fired. **Fail closed** on any
miss — do not present or deliver a pack that fails the output check.

## Human approval
`external-delivery`: human review is required before the findings pack is delivered outside
the preparation team or written to a case/system of record. No approval is needed for the
preparer's own read. The skill never certifies, signs off, files, or submits — and never
posts a GL correction.

## Failure handling
- **Missing mandatory cells** → report as a `completeness` finding (blocking); do not
  synthesize values.
- **Missing lineage / `source_refs`** → `lineage_completeness` finding; the cell is not
  filing-traceable.
- **No prior period** → variance-vs-prior is `not_evaluable`; state so; do not infer trend.
- **No config block** → default thresholds are used; record the `config_version` and flag
  that defaults were applied.
- **Reconciliation source unavailable / stale** → mark the tie-out `not_evaluable` and cite
  the gap; never assume a tie.
- **Ambiguous report/entity/period** → stop and confirm; never validate the wrong filing.
- **Tool timeout** → return the checks completed so far with a clear "incomplete" flag; do
  not emit a `Clear` band from a partial run.

## Output contract
1. **Summary** — report code, entity (masked), period, due date, count of blocking vs.
   advisory findings, readiness band.
2. **Findings** — per fired check: name, plain-language reason, status, evidence rows
   (cited), and the basis (threshold/tolerance/expected).
3. **Remediation next-steps** — non-authoritative suggestions (e.g., route a break to
   `gl-reconciler`, obtain the missing approver sign-off, document the variance driver).
4. **Data gaps / not-evaluable checks.**
5. **Machine-readable** — findings + evidence + `validation_id` for downstream skills.
6. **Standing disclaimer** — "Validation findings and cited evidence only; not a filing
   determination, certification, or submission. No regulatory report has been certified,
   signed off, filed, or submitted."
See [references/controls.md](references/controls.md).

## Privacy and records
Confidential financial records. Mask entity identifiers (e.g., last segment of an RSSD/LEI)
and minimize data in the output to what evidences a finding. Retain the findings pack +
citations + `config_version` per records policy; log the read and any external-delivery
approval. Never exfiltrate financial data or draft numbers outside approved channels.

## Gotchas
- **A finding is not a filing decision.** A `Clear` band means "no deterministic exceptions
  found" — it is **not** an approval to file. Human sign-off and authorized submission are
  always still required.
- **Tolerance is config, not judgment.** Reconciliation and edit-check tolerances come from
  the versioned config; do not loosen a tolerance to make a break disappear.
- **Sign-off timing.** A sign-off dated *before* the data `as_of`, or a preparer who is also
  the approver, is an evidence exception even if all roles are "present".
- **Variance ≠ error.** A period-over-period spike is an **analytical-review flag** inviting
  an explanation (acquisition, reclassification, seasonality), not a data error — keep it
  advisory.
- **Restatements & sub-schedules.** A prior-period restatement can make variance checks fire
  spuriously; note when the prior figure was restated and treat the flag as evaluable-with-context.
- **Do not net breaks.** Two offsetting reconciliation breaks are two findings, not zero;
  never net them to hide the exceptions.
