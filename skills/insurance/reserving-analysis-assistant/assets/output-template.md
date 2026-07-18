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

Data gaps (force `needs-data`): {{data_gaps}}. Anomalies raised for actuarial review (force
`anomaly-flagged`): {{anomalies}}.

## 3. Development method and factors

Method: {{method}} (approved: volume-weighted or simple-average chain-ladder). Tail factor:
{{tail_factor}} ({{tail_basis}}).

| Development period | Age-to-age factor | Basis |
| ------------------ | ----------------- | ----- |
| {{from_age}}→{{to_age}} | {{factor}} | {{factor_basis}} |

Cumulative development factors to ultimate: {{cdf_table}}.

## 4. Indicated ultimate and IBNR

Indicated figures are mechanical method outputs, not selected reserves. IBNR =
indicated ultimate − reported. Every row ties out (ultimate = reported + IBNR).

| Origin | Latest dev age | Reported ({{unit}}) | CDF used | Indicated ultimate | Indicated IBNR | Source |
| ------ | -------------- | ------------------- | -------- | ------------------ | -------------- | ------ |
| {{origin}} | {{latest_dev_age}} | {{reported}} | {{cdf_used}} | {{ultimate}} | {{ibnr}} | {{citation}} |
| **Total** | | {{total_reported}} | | {{total_ultimate}} | {{total_ibnr}} | |

Selection basis: {{selection_basis}} — the appointed actuary selects the carried reserve.

## 5. Severity, frequency, and large-loss analysis

| Metric | Value | Source |
| ------ | ----- | ------ |
| Ultimate severity (ultimate losses / ultimate counts) | {{severity}} | {{severity_source}} |
| Frequency (ultimate counts / earned exposure) | {{frequency}} | {{frequency_source}} |
| Large-loss threshold | {{large_loss_threshold}} | ruleset |
| Large losses ≥ threshold (count / total) | {{ll_count}} / {{ll_total}} | {{ll_source}} |

Large-loss claims flagged for the actuary's attention: {{large_loss_claims}}. Where a
large loss distorts the triangle, note it here; do not silently smooth it.

## 6. Uncertainty and sensitivity

Indicative sensitivity only — a min-max link-ratio range, **not** a statistical confidence
interval and **not** a reserve range opinion.

| Measure | Value |
| ------- | ----- |
| Low indicated ultimate (min link ratios) | {{low_ultimate}} |
| Selected-method indicated ultimate | {{selected_ultimate}} |
| High indicated ultimate (max link ratios) | {{high_ultimate}} |
| Indicative range (% of selected) | {{range_pct}} |

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
