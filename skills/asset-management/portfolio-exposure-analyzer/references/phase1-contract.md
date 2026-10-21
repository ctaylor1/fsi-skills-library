# Phase 1 offline contract

Require positive authoritative nav and nav_source_ref. Supplied holdings/NAV differences are disclosed; no cash is inferred. Complete measurement tables retain home country and limit-exempt assets; exemptions apply only to screens. Missing classifications and partial one-level look-through remain explicit UNKNOWN residuals with dimension_coverage. Wrapper asset-class totals preserve full positions. Nested/overweight/negative look-through and short holdings are unsupported and fail. Missing liquidity prevents an asserted whole-book illiquid percentage. Duration remains limited to supplied corporate/government-bond measures; factors are supplied loadings, not priced risk sensitivities.

## Source-bound validation

The native scripts consume supplied JSON and produce an offline analytical result. They do not connect to books of record, queue alerts, authenticate sources, approve a model, grant a mandate exception or authorize delivery. `input_hash` covers the complete supplied input; `source_truth: unverified` distinguishes reproduction from source authentication. `inputs_hash` is a compatibility alias. Run identifiers include the complete-input digest.

Retain the original input separately. Validate the calculated native result with:

```sh
python scripts/validate_output.py evals/files/pack_example.json --input evals/files/portfolio_example.json
```

The output validator reruns the native calculation against the original input, in addition to domain arithmetic/control checks. It rejects altered results, changed inputs, omitted original evidence and extra fields. A free-form narrative or containing workflow envelope belongs in a separate reviewed artifact; it cannot be appended to the native result as if source-validated. Standalone internal consistency is insufficient for release.

All real dates and finite numeric inputs are checked. Missing facts are not supplied by the source-binding mechanism. Explicit sample fixtures are synthetic; passing their deterministic checks does not demonstrate production quality, jurisdictional completeness, independent professional acceptance or live integration behavior.

## Validation scope

`python tools/test_asset_management_investment_phase1.py` from the repository root exercises cross-input substitution, altered outputs, domain regressions and the ten native golden inputs. Each package's `evals/evals.json` retains its script-level positive/negative checks; source-bound output commands include `--input`. Natural-language trigger and professional-use evaluations remain separately authored scenarios, not an executed acceptance claim.
