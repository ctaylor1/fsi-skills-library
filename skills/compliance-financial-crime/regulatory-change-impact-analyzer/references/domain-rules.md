# Regulatory Change Impact Analyzer — Phase 1 method

- Record authority type, lifecycle (`proposed`, `adopted`, `effective`, `stayed`, `withdrawn`, `superseded`, `unknown`), status-as-of and publication date. Keep commencement and compliance deadlines separate. Approved/adopted does not mean currently applicable.
- Entity, activity, product, threshold, exemption and cross-border nexus require an explicit supplied applicability assessment. Jurisdiction/business-line matching is only a screening hint. Missing review evidence remains `unknown`, including mismatching or absent scope facts.
- Review policy, control, system, data, training and owner mappings for applicable or unresolved obligations. A justified mapping exception is not silently treated as missing coverage.
- Only an active binding requirement, supplied applicable assessment, elapsed compliance deadline and sourced incomplete implementation produce an elapsed-deadline finding. Already effective is not synonymous with overdue; unknown implementation is unevaluable. Guidance and proposed/stayed changes do not generate legal-breach conclusions.
- Future deadlines produce readiness analysis. Declared authority conflicts are routed, not resolved or independently discovered by the calculator.

## Supplied schema

`change_id`, `as_of`, `config_version`, `instrument`, extracted `obligations`, `firm_profile`, and optional `inventory.mappings`. Each non-unknown applicability assessment records status, rationale, source reference, reviewer and review date. Implementation assertions require a source reference.

The authoritative executable shape check is `scripts/validate_input.py`. `scripts/calculate_or_transform.py`
contains the bounded calculation. The worked source fixture is `evals/files/change_example.json`;
it is explicitly synthetic and must not be used as current law or institutional policy.

No current regulatory corpus, horizon-monitoring scheduler, legal rule pack, operational integration or primary-text truth verification is bundled. All lifecycle and applicability evidence is supplied and subject to professional review.
