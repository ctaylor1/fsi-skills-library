# Native schema — 0.2.0

Require legal issuer ID, ticker, reporting period, economic as_of, reporting currency, config version, estimate_source label, aware release_at and knowledge_cutoff at/after release, and nonempty metrics. Each metric requires finite actual, cited actual_ref, actual_known_at within the post-release cutoff, unit, period_ref, accounting_basis and allowed direction. Estimate may be null. Evaluable comparisons require estimate_ref, frozen aware estimate_known_at before release, and explicit matching estimate_period/unit/accounting_basis/currency. Duplicate metric names are rejected: the native schema represents one baseline per metric. Tolerances must be finite nonnegative numbers.

## Output and partial coverage

Metric findings retain actual evidence even if surprise is withheld, including a not_evaluable reason for absent/zero estimate or missing cited frozen vintage. Guidance and transcript evidence gaps withhold their findings rather than generating references containing None. Current and prior guidance citations survive. Overall_result describes the available headline findings, not a security view. `baseline_scope` explicitly records the one-baseline limitation; reporting currency, issuer and cutoff metadata survive.

All outputs include canonical `input_hash` over the complete original JSON and `source_truth: unverified`; no embedded `source_input` is accepted. Keep the original separately. Finite JSON, domain guards and input shape validation run before computation. Output validation requires `--input` (self-test retains its fixture original) and reconstructs every native field. Added narrative is a separate reviewed artifact, not a permitted unchecked field.
