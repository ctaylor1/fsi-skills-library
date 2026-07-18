# AI Evaluation Benchmark — DRAFT (for model-risk-governance review)

> Draft evaluation benchmark for human review only; this skill does not run the evaluations,
> does not score or certify the model, and makes no go/no-go, release, or compliance
> determination — every threshold and baseline must be approved by model risk governance
> before use.

Fill every `{{placeholder}}` from validated sources. Do not assert a threshold or baseline
that is not traced to an approved source; mark any placeholder value `proposed`. Do not add
pass/fail results, a release recommendation, or certification language.

## 1. System under evaluation

| Field | Value |
| ----- | ----- |
| Model / agent id | {{model_id}} |
| Name | {{name}} |
| Version | {{version}} |
| Use case | {{use_case}} |
| Inherent risk rating | {{risk_rating}} |
| Registry reference | {{registry_ref}} |
| Methodology / threshold catalog version | {{spec_version}} |
| As of | {{as_of_date}} |

## 2. Coverage vs required dimensions

Required for a **{{risk_rating}}**-risk system: {{required_dimensions}}.
Present: {{present_dimensions}}. Missing (keeps package draft-incomplete): {{missing_required}}.
Coverage complete: {{coverage_complete}}.

## 3. Evaluation specifications

One row per evaluation. `Acceptance` and `Baseline` show the value **and** its provenance
(`approved` with a source, or `proposed` pending calibration). No value without provenance.

| Eval id | Dimension | Dataset (representative) | Metric (direction) | Acceptance rule | Baseline | Sample / min | Status |
| ------- | --------- | ------------------------ | ------------------ | --------------- | -------- | ------------ | ------ |
| {{eval_id}} | {{dimension}} | {{dataset_ref}} | {{metric}} ({{metric_direction}}) | {{operator}} {{threshold_value}} — {{threshold_provenance}} ({{threshold_source_id}}) | {{baseline_value}} — {{baseline_provenance}} ({{baseline_source_id}}) | {{sample_size}} / {{min_sample}} | {{status}} |

Status legend: `ready-for-review` (dataset + approved threshold + approved baseline + adequate
sample + consistent direction) · `needs-calibration` (threshold/baseline not approved-sourced)
· `insufficient-sample` (below documented minimum) · `direction-mismatch` (operator contradicts
metric direction) · `needs-data` (missing dimension/dataset/metric).

## 4. Open items before the benchmark can be run

- [ ] Every `proposed` threshold and baseline approved by governance and re-sourced.
- [ ] Every `needs-data` evaluation given a representative, lineage-checked dataset.
- [ ] Every `insufficient-sample` evaluation resized to at least its documented minimum.
- [ ] Every `direction-mismatch` corrected so the operator matches the metric direction.
- [ ] Required-dimension coverage completed for the system's risk rating.

## 5. Approvals (required before any use)

| Field | Value |
| ----- | ----- |
| Governance approval | {{governance_approval}} (must be `pending` from this skill) |
| Reviewer sign-off required | {{reviewer_signoff_required}} |
| Approver role | {{approver_role}} |

- [ ] Dimensions, datasets, and representativeness reviewed.
- [ ] Acceptance thresholds and baselines approved and traced to an approved source.
- [ ] Sample sizes and methodology (`spec_version`) confirmed.
- [ ] Benchmark approved for execution by the named authorized body (not this skill).

Reviewer: ________________________  Date: ____________  Decision: approve / revise / reject

## 6. Standing note

Draft evaluation benchmark for human review only; this skill does not run the evaluations,
does not score or certify the model, and makes no go/no-go, release, or compliance
determination — every threshold and baseline must be approved by model risk governance before
use.
