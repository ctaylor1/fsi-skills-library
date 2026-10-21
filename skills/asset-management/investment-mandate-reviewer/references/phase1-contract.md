# Phase 1 offline contract

Each rule needs source_ref and explicit applies_to (all_portfolios:true or mandate_ids/portfolio_ids); portfolios require mandate_id and holdings_source_ref. Optional effective_from/effective_to control rule dates. target_bucket (or the scope-named field, such as asset_class) selects the intended bucket, including zero exposure for absent buckets. Both maximum and minimum bounds are tested, including supplied pre-trade deltas and already-breached exposures. Unsupported scopes/methods and missing classifications produce not_evaluable rule_results. Regulatory simple limits require method:simple_limit; this does not implement complex statutory diversification. ESG holdings tests remain supported; ESG pre-trade results are explicitly unavailable. Proposed trades need side, value, source_ref and as_of. Projections hold NAV constant and do not infer cash legs, FX, derivatives or order sequencing. Prices and holdings retain their own freshness; status changes preserve incident identity.

## Source-bound validation

The native scripts consume supplied JSON and produce an offline analytical result. They do not connect to books of record, queue alerts, authenticate sources, approve a model, grant a mandate exception or authorize delivery. `input_hash` covers the complete supplied input; `source_truth: unverified` distinguishes reproduction from source authentication. `inputs_hash` is a compatibility alias. Run identifiers include the complete-input digest.

Retain the original input separately. Validate the calculated native result with:

```sh
python scripts/validate_output.py evals/files/pack_example.json --input evals/files/run_example.json
```

The output validator reruns the native calculation against the original input, in addition to domain arithmetic/control checks. It rejects altered results, changed inputs, omitted original evidence and extra fields. A free-form narrative or containing workflow envelope belongs in a separate reviewed artifact; it cannot be appended to the native result as if source-validated. Standalone internal consistency is insufficient for release.

All real dates and finite numeric inputs are checked. Missing facts are not supplied by the source-binding mechanism. Explicit sample fixtures are synthetic; passing their deterministic checks does not demonstrate production quality, jurisdictional completeness, independent professional acceptance or live integration behavior.

## Validation scope

`python tools/test_asset_management_investment_phase1.py` from the repository root exercises cross-input substitution, altered outputs, domain regressions and the ten native golden inputs. Each package's `evals/evals.json` retains its script-level positive/negative checks; source-bound output commands include `--input`. Natural-language trigger and professional-use evaluations remain separately authored scenarios, not an executed acceptance claim.
