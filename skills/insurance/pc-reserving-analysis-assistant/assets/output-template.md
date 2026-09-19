# Reserve Analysis Exhibit — DRAFT (for qualified actuarial review)

> Draft reserving analysis for qualified actuarial review only; this skill computes
> method-indicated estimates from the supplied data, does not select or book carried
> reserves, does not issue or sign a Statement of Actuarial Opinion, and does not opine on
> reserve adequacy — a qualified actuary must review, select, and approve every figure
> before use.

Fill every `{{placeholder}}` from validated triangle data. Do not add a figure or statement
that is not tied to a listed source. Report method **indications** only; never assert that a
reserve is adequate, sufficient, or final, and never state that anything has been booked,
filed, or opined. The eight numbered sections below are required and are checked by
`scripts/validate_output.py`.

## 1. Cover and valuation basis

| Field | Value |
| ----- | ----- |
| Valuation date | {{valuation_date}} |
| Dataset version | {{dataset_version}} |
| Currency / unit | {{currency}} / {{unit}} |
| Segments in scope | {{segment_list}} |
| Basis (paid / incurred) per segment | {{basis_by_segment}} |
| Prepared by | {{preparer}} |

## 2. Data sources and reconciliation

Every triangle, count, exposure, and large-loss figure is sourced. Cite each with
`{system}:{ref}@{date/version}`.

| Segment | Triangle source | As-of / version | Reconciles to |
| ------- | --------------- | --------------- | ------------- |
| {{segment_id}} | {{triangle_source}} | {{as_of}} | {{recon_target}} |

Triangle gaps preventing development (`needs-data`): {{data_gaps}}. Anomalies raised for
actuarial review (`anomaly-flagged`): {{anomalies}}. Supporting analyses that remain
unevaluable despite a computable triangle indication: {{supporting_analysis_gaps}}.

## 3. Development method and factors

Method: {{method}} (approved: volume-weighted or simple-average chain-ladder). Tail factor:
{{tail_factor}} ({{tail_basis}}).

| Development period | Age-to-age factor | Basis |
| ------------------ | ----------------- | ----- |
| {{from_age}}→{{to_age}} | {{factor}} | {{factor_basis}} |

Cumulative development factors to ultimate: {{cdf_table}}.

## 4. Indicated ultimate and reserve measures

Indicated figures are mechanical method outputs, not selected reserves. Choose labels and
values for the segment's basis: paid triangles use **Paid** (`paid`) and **Total unpaid**
(`total_unpaid`); incurred triangles use **Reported incurred** (`reported_incurred`) and
**IBNR** (`ibnr`). Total unpaid includes case outstanding and must not be relabeled IBNR.
Every row ties out as ultimate = paid + total_unpaid or reported_incurred + ibnr.

| Origin | Latest dev age | {{diagonal_label}} ({{unit}}) | CDF used | Indicated ultimate | Indicated {{reserve_measure_label}} | Source |
| ------ | -------------- | ------------------- | -------- | ------------------ | -------------- | ------ |
| {{origin}} | {{latest_dev_age}} | {{diagonal_value}} | {{cdf_used}} | {{ultimate}} | {{reserve_value}} | {{citation}} |
| **Total** | | {{total_diagonal}} | | {{total_ultimate}} | {{total_reserve_value}} | |

Selection basis: {{selection_basis}} — the appointed actuary selects the carried reserve.

## 5. Severity, frequency, and large-loss analysis

| Metric | Value | Source |
| ------ | ----- | ------ |
| Supplied-count severity (indicated ultimate losses / supplied claim counts) | {{severity}} | {{severity_source}} |
| Frequency (supplied claim counts / earned exposure) | {{frequency}} | {{frequency_source}} |
| Supplied claim-count basis | {{count_basis}} | {{count_source}} |
| Large-loss threshold | {{large_loss_threshold}} | ruleset |
| Large losses ≥ threshold (count / total) | {{ll_count}} / {{ll_total}} | {{ll_source}} |

Large-loss claims flagged for the actuary's attention: {{large_loss_claims}}. Where a
large loss distorts the triangle, note it here; do not silently smooth it.
Supplied counts are not developed ultimate counts; state their basis and its compatibility
with the loss and exposure data. If the large-loss schedule or threshold is unavailable,
report the analysis as `not_evaluable` with unknown count, total and flag; do not fill these
cells with zero. Keep that supporting-data gap visible in the partial artifact.

## 6. Uncertainty and sensitivity

Indicative sensitivity only — a min-max link-ratio range, **not** a statistical confidence
interval and **not** a reserve range opinion.

| Measure | Value |
| ------- | ----- |
| Low indicated ultimate (min link ratios) | {{low_ultimate}} |
| Method-indicated ultimate | {{selected_ultimate}} |
| High indicated ultimate (max link ratios) | {{high_ultimate}} |
| Indicative range (% of method-indicated ultimate) | {{range_pct}} |

## 7. Assumptions and limitations

- Method, tail, and segmentation assumptions with their rationale: {{assumptions}}.
- Known limitations (data maturity, mix change, large-loss distortion, trend): {{limitations}}.
- This analysis does not select reserves, does not opine on adequacy, and does not book or
  file anything. It is an input to actuarial judgment.

## 8. Actuarial review and approval

Required sign-offs (all **pending** until a human completes them; the skill never
self-approves):

- [ ] Preparing analyst / actuarial associate — data and computations checked.
- [ ] Qualified (appointed) actuary — method, factors, and indications reviewed; carried
      reserve selected; adequacy assessed under separate authority.
- [ ] Independent peer reviewer — actuarial review complete.

Reviewer: ________________________  Date: ____________  Decision: accept / revise / return
