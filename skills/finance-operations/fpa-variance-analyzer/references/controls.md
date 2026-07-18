# Controls — fpa-variance-analyzer

- **Risk tier:** R2 — analytical. **Action mode:** Read-only analysis.
- **Human approval:** `external-delivery` — required before the commentary goes to business
  leaders, a board/management pack, or a system of record. Internal analytical use may be
  reviewer-sampled.

## Prohibited (fail closed)

- No **management decision** or directive: cut/add/freeze headcount, defund/approve/reject a
  program or budget. Describe the variance; attribute the decision to management.
- No **forecast/guidance commitment**: reforecast as the official number, commit to a target,
  or state the company "will hit/deliver/beat" a figure.
- No **restatement of actuals**, **journal/adjustment posting**, or any system-of-record write
  — route to `gl-reconciler` (breaks/corrections) or `month-end-close-orchestrator` (posting)
  and a human.
- No **personalized investment, tax, or legal advice**.
- No **config tuning to an individual line** to change whether it is flagged material.
- No **fabricated driver decomposition** to force an attribution tie-out.

## Required output screens (`scripts/validate_output.py`)

- Every material finding has ≥ 1 cited evidence row (actual + compared base, plus driver rows).
- Driver attribution `ok` is independently reproducible: `sum(drivers)` ties out to `vs_budget`
  within `attribution_tolerance`.
- Every non-zero run-rate impact is labeled an estimate (`run_rate_is_estimate: true`).
- `suggested_priority` equals the deterministic mapping from the material-finding set.
- No decision/commitment/restatement/advice language (regex screen over narrative + notes +
  per-finding commentary; the disclaimer and caveats fields are exempt from the screen).
- Standing disclaimer present.
- Caveats (alternative-explanation prompts) included when any finding is material.

Fail closed on any miss.

## Fairness / conduct

- Describe variances factually; do not assign blame to a named individual or team.
- Do not use the analysis to justify a predetermined conclusion; report what the numbers show.

## Data classification, privacy, records

- **Confidential (financial records).** Minimize data to what evidences a material finding.
- Salary/compensation lines: report at the aggregate account level; do not expose individual
  pay in commentary.
- Retain the analysis + citations + `config_version` per records policy; log the read and any
  external-delivery approval. Never exfiltrate financial data to an unapproved destination.

## Reproducibility

`analysis_id` binds the output to the exact inputs, `basis`, and **config version**; re-running
with the same inputs and config reproduces the variances, materiality flags, attribution
statuses, run-rate impacts, and suggested priority.
