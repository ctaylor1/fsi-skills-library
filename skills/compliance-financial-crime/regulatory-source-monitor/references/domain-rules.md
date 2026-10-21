# Domain method and schema

Snapshots are indexed by `(source_id, instrument_id)`. Version/hash differences produce `revised`, new keys `new`, and baseline-only keys `missing_current_observation`. Legal lifecycle is read from the exact supplied fact and never inferred from disappearance. Coverage is `complete` only against the supplied expected source universe with supported `complete` collection outcomes and current observations; partial/unknown/missed sources remain explicit. Event publication/effective/compliance chronology and supersession self-links/cycles are reviewed.

## Common evidence contract

Read `scripts/foundation_contract.py` for the exact common contract and [evidence contract](evidence-contract.md) for professional provenance. Every consequential input uses a claim `{value, source_refs, fact_ids}` with exact registry facts; records cannot cite an unrelated source field to establish their own status. Common validation retains stale/conflicting/missing evidence and requires detached original input. Unsupported legal profiles and methods remain open.

## Native payload

`expected_sources`: nonempty unique IDs. `collections`: `{source_id, outcome_fact, observed_on_fact}`. `baseline`, `current`: lists `{source_id, instrument_id, version, content_hash, lifecycle_fact, published_date_fact, effective_date_fact, compliance_date_fact, observed_on_fact, snapshot_fact, supersedes}`. Dates are ISO values inside exact supporting facts; `supersedes` names instrument IDs and conveys only supplied relationships.

The fixture in `evals/files/input.json` is de-identified synthetic supplied policy and illustrative evidence. It does not assert a real institution, live rule, independently tested control or actual legal acceptance. The native result retains detached claim-path/source/fact locators and consistency states; these locators do not establish semantic truth or automatic conclusion support. Domain findings preserve their open issues.

## Practitioner questions

Which entity, activity, population and date does each finding concern? Who owns the extracted source text and contested interpretation? What material evidence is missing or conflicting? Which conclusion is a fact, supplied institutional policy, method assumption or recommendation? What adjacent specialist must review before this artifact can be relied upon?

`snapshot_fact.value` exactly equals `{source_id, instrument_id, version, content_hash, supersedes}` for that snapshot. Observation dates must be real calendar dates and within the cutoff; baseline observations later than current observations remain chronology gaps. Source collection outcomes are supplied collection evidence, not verified absence of new law.
