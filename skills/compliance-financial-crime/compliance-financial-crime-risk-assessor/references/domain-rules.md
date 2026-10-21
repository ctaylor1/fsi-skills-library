# Domain method and schema

Supported bounded method is `weighted-multiplicative-v1`: inherent indicator = Σ(weight × inherent)/Σ(weight); residual = Σ(weight × inherent × (1 − supplied control factor))/Σ(weight). Scale minimum/maximum, dimension universe, weights and acceptance are explicit supplied policy. Factors range 0..1 and require supported design/operating/testing evidence; no factor is inferred from a control name. Missing/conflicting evidence or unaccepted method suppresses aggregation/residual. This illustrative accepted-method implementation is not law or calibrated risk.

## Common evidence contract

Read `scripts/foundation_contract.py` for the exact common contract and [evidence contract](evidence-contract.md) for professional provenance. Every consequential input uses a claim `{value, source_refs, fact_ids}` with exact registry facts; records cannot cite an unrelated source field to establish their own status. Common validation retains stale/conflicting/missing evidence and requires detached original input. Unsupported legal profiles and methods remain open.

## Native payload

`method`: `{name, version, acceptance_fact, definition_fact, dimensions, weights, scale_min, scale_max}`. `assessments`: nonempty `{dimension, inherent_fact, control_factor_fact, design_evidence_fact, operating_evidence_fact, testing_evidence_fact}`. `scope_fact` records population/entity/period. Exact required dimensions and weights must match; zero-weight dimensions are not allowed to vanish.

The fixture in `evals/files/input.json` is de-identified synthetic supplied policy and illustrative evidence. It does not assert a real institution, live rule, independently tested control or actual legal acceptance. The native result retains detached claim-path/source/fact locators and consistency states; these locators do not establish semantic truth or automatic conclusion support. Domain findings preserve their open issues.

## Practitioner questions

Which entity, activity, population and date does each finding concern? Who owns the extracted source text and contested interpretation? What material evidence is missing or conflicting? Which conclusion is a fact, supplied institutional policy, method assumption or recommendation? What adjacent specialist must review before this artifact can be relied upon?

`definition_fact.value` exactly equals the method name/version/dimensions/weights/scale_min/scale_max object. A bare acceptance flag cannot support changed method parameters. The helper computes no fixed low/medium/high categories or risk-appetite thresholds.
