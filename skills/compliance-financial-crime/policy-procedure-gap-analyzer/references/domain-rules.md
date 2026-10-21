# Policy Procedure Gap Analyzer — Phase 1 method

- Explicit applicability is required for a clean result. Unknown applicability stays unevaluable; a supplied false value is informational and retains its review responsibility.
- Future-effective requirements are assessed for readiness; findings carry `future_readiness` instead of being discarded. Present findings carry `current_design`. Neither is an adjudicated regulatory breach.
- The three supported comparator pairs are retention minimum years versus retention years, maximum reporting threshold USD versus reporting threshold USD, and maximum training interval months versus training interval months. They are supplied requirement parameters, not universal legal thresholds.
- Missing or unsupported control parameters remain unevaluable. Such requirements cannot appear in `clean_requirements`. Missing/future control-review dates and other control findings also prevent a clean label for mapped requirements.
- An evidence pointer records where an artifact is said to exist. It never proves source truth, design sufficiency beyond these checks, operating effectiveness, sampling adequacy or control execution. `operating_effectiveness_status` is always `not_assessed`.

## Supplied schema

Supplied framework/jurisdiction, assessment date/config version, requirements with citations/criticality/applicability/effective dates, policy-control mappings, review dates and optional parameter objects. Numeric parameters must be finite. `clean_requirements` means no detected design issue within supported checks, not compliance.

The authoritative executable shape check is `scripts/validate_input.py`. `scripts/calculate_or_transform.py`
contains the bounded calculation. The worked source fixture is `evals/files/analysis_example.json`;
it is explicitly synthetic and must not be used as current law or institutional policy.

Only the documented comparator types and document/mapping checks are implemented. No operational samples are evaluated; no wording is approved, finding closed, report filed or policy edited.
