# Phase 1 offline contract

The implemented method is single-period arithmetic Brinson-Fachler with an explicitly additive local-plus-FX convention; it excludes the local/FX cross term. Portfolio and benchmark weights must each sum to one. Missing returns remain needs-data. This is not TWR/MWR measurement, multiperiod linking, exact multicurrency attribution, composite administration or private-fund performance. GIPS compliance and verification are distinct: independent verification is recommended, not a prerequisite for claiming compliance. The agent does not establish either status.

## Source-bound validation

The native scripts consume supplied JSON and produce an offline analytical result. They do not connect to books of record, queue alerts, authenticate sources, approve a model, grant a mandate exception or authorize delivery. `input_hash` covers the complete supplied input; `source_truth: unverified` distinguishes reproduction from source authentication. `inputs_hash` is a compatibility alias. Run identifiers include the complete-input digest.

Retain the original input separately. Validate the calculated native result with:

```sh
python scripts/validate_output.py evals/files/attribution_example.json --input evals/files/attribution_intake_example.json
```

The output validator reruns the native calculation against the original input, in addition to domain arithmetic/control checks. It rejects altered results, changed inputs, omitted original evidence and extra fields. A free-form narrative or containing workflow envelope belongs in a separate reviewed artifact; it cannot be appended to the native result as if source-validated. Standalone internal consistency is insufficient for release.

All real dates and finite numeric inputs are checked. Missing facts are not supplied by the source-binding mechanism. Explicit sample fixtures are synthetic; passing their deterministic checks does not demonstrate production quality, jurisdictional completeness, independent professional acceptance or live integration behavior.

## Validation scope

`python tools/test_asset_management_investment_phase1.py` from the repository root exercises cross-input substitution, altered outputs, domain regressions and the ten native golden inputs. Each package's `evals/evals.json` retains its script-level positive/negative checks; source-bound output commands include `--input`. Natural-language trigger and professional-use evaluations remain separately authored scenarios, not an executed acceptance claim.

Primary standard: [CFA Institute GIPS verification guidance](https://www.gipsstandards.org/standards/gips-standards-for-verifiers/) (reviewed 2026-09-20).
