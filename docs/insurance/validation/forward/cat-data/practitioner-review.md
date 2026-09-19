# Independent forward evaluation: catastrophe monitoring and insurance data reconciliation

Date: 2026-09-18. Synthetic supplied snapshots only; no external feeds, model calls, source mutations or external delivery.

The packages were copied into this directory before execution. Only SKILL.md, domain rules, source map, shared contract and actual runtime scripts were read. Phase/audit documents, eval fixtures, regression tests and expected outputs were not consulted. The original reconciliation package folder was `actuarial-data-lineage-checker`; its artifact producer is `insurance-data-reconciler`. `snapshot-hashes.json` records the copied instructions and scripts. No repository files were edited.

Eight raw business requests were mapped to the packages' native schemas with explicit synthetic capacity, represented carrier, portfolio/dataset identity, as-of, versioned sources, configuration and financial basis. CAT model rows carry event, footprint, exposure, model-run and common scenario identities. Reconciliation paid/incurred meaning is represented through distinct definition versions because the native schema uses a metric-definition identifier rather than a separate paid/incurred field.

Each directory under `runs/` retains raw-request.txt, input.json, output.json, the command/exit/stdout/stderr records for native input validation, calculation and output validation, and a fourth validation calling `validate(output, original_input)`. All 32 command stages exited 0. That proves repeatability and package-validator acceptance for these fixtures; the output validation calls the same calculator and is not independent semantic validation.

## Practitioner-facing results

| Run | Interpretation of the evidence |
|---|---|
| `cat_complete_exposed` | Two exposed locations each have USD 12m allocated gross limits and USD 16m TIV. Zone accumulation is USD 24m, separate TIV is USD 32m, and the common named low/mid/high scenarios total USD 9m/21m/36m. Zone ratio 24/20 and high-scenario ratio 36/30 are both 1.2, producing two Watch alerts. Each single-location ratio is 12/15 = 0.8, below the 0.9 approach boundary. The deterministic calculations match the supplied assumptions. These are aligned scenarios, not PML or quantiles. |
| `cat_event_feed_unavailable` | Today's footprint cannot be evaluated. Both prior alert keys remain unknown; none is cleared. No metric is computed. The run is partial/not_evaluable with severity Unknown and a missing event-feed explanation. Preserve the two alerts for a reviewer when the feed returns. |
| `cat_exposure_feed_unavailable` | Today's exposure cannot be measured. Both prior alerts remain unknown and severity is Unknown. However, the output also presents zero zone accumulation, zero TIV and a zero exceedance ratio in evaluated_metrics, with a citation of `unknown`; those numbers are not measured exposure and must not be used as an observed zero. See finding C1. |
| `cat_one_exposed_location_unmodeled` | Complete exposure still supports the USD 24m zone Watch alert. LOC-2 has no model result, so a complete event scenario total is unavailable. The prior event-model alert remains unknown. The script correctly withholds the event total instead of presenting LOC-1's USD 12m high result as the total. The location gap and reason are explicit. |
| `cat_complete_no_exposed_locations` | Both current locations are outside the current footprint. The declared complete portfolio supports measured zero zone exposure and the zone alert clears. No modeled-loss metric is emitted, so the prior event-model alert remains unknown. The package nevertheless claims complete/evaluable, normal confidence, severity None and no unresolved issues. The headline must not be treated as an all-clear while that alert is retained unknown. See finding C2. |
| `reconciliation_conflicting_duplicates_and_basis` | Current USD net paid losses of 1.1m and 1.35m are conflicting duplicate observations. Prior EUR gross incurred losses of 2m are a different definition, currency and basis. No percentage or absolute movement is meaningful here. The script reports one duplicate break and withholds every comparison. The reviewer must resolve both source ambiguity and economic comparability; the generated packet reports only the duplicate and cites only its first row. See D1 and limitation D2. |
| `reconciliation_incompatible_basis_isolated` | With one current record in this controlled isolate, the script reports `not_comparable` for definition_version, currency and financial_basis, cites current and prior observations, and calculates no movement. It performs no FX conversion and does not conflate net paid with gross incurred. Removing a row for this isolated fixture is not a decision about which real source is correct. |
| `reconciliation_conflicting_duplicates_isolated` | With matching USD/net/paid definitions on the two snapshots, duplicate current records still block movement. No row wins arbitrarily and no apparent 10% or 35% movement is emitted. The duplicate evidence contains only the first source reference. |

## Concrete findings

### C1 — Missing exposure becomes numeric zero inside evaluated metrics (P2)

Reproduction: `runs/cat_exposure_feed_unavailable/input.json` removes the policy-admin source and all location records, and marks `data_coverage.exposures` unavailable. The event footprint and other source/config metadata remain present. Run the retained command in `calculate_or_transform.py.result.json`.

Observed output: `evaluated_metrics[0]` has `metric: "0"`, `aggregate_tiv: "0"`, `exceedance_ratio: "0"`, `location_count: 0`, and evidence `[{"citation":"unknown","zero_observed_locations":true}]`. The same numeric evaluation is attached to the unknown zone alert. Native output validation and input-bound recomputation both accept it. Run-level unknown/partial status and retention of the two alerts are correct and reduce the harm, but consumers of the metric table receive an invented zero rather than an unavailable observation.

Cause: snapshot `packages/catastrophe-exposure-monitor/scripts/calculate_or_transform.py:120-129` emits every footprint-zone metric after checking only financial-context validity; summing an empty set returns Decimal(0) even when the entire exposure source is absent. `:181` then calls the run partially evaluable solely because this metric exists.

Domain expectation: the package contract says unknown never becomes zero and a model/source cannot replace missing exposure evidence. Gate measured zone observations on exposure availability, or encode unavailable values/evaluability explicitly. Retain the unknown prior alert. Distinguish unavailable data from a complete portfolio whose locations are all outside a footprint.

### C2 — All-clear headline coexists with an unevaluated retained prior alert (P2)

Reproduction: `runs/cat_complete_no_exposed_locations/input.json` has the same event, complete fresh versioned sources and the two complete current location records, now outside the event footprint. It retains the zone and event-model alert keys from the complete exposed baseline.

Observed output: `dedup` is cleared=1 and unknown=1. The modeled-loss prior alert has `status: "unknown"` and `evaluation: null`. At the same time, `overall_severity` is `"None"`, `confidence` is `"normal"`, `completeness` is `"complete"`, `evaluability` is `"evaluable"`, and `unresolved_issues` is empty; the artifact repeats complete/evaluable. Both output validators accept it. A headline-only consumer receives an all-clear despite a retained, unevaluated prior metric.

Cause: `calculate_or_transform.py:161` determines completeness before processing prior alerts. `:167-172` creates unknown prior alerts without adding an issue or downgrading evaluability. `:176-182` derives the summary solely from active alerts and the earlier completeness flag. No event modeled-loss metric is constructed for zero exposed locations at `:152` because `models` is empty.

Bounded expectation: the measured zero zone observation can validly clear its zone alert. The treatment of a no-exposure event modeled-loss alert needs a defined rule. Under the package's current choice to retain it unknown, the summary/artifact must carry that unresolved status. An independently specified evidenced-zero model convention would be a different possible design; this evaluation does not infer one.

### D1 — Duplicate finding omits the conflicting record's evidence (P2, review usability)

Reproduction: `runs/reconciliation_conflicting_duplicates_and_basis/input.json` contains current row references ending `/row/1` (1.1m) and `/row/2` (1.35m) with the same row grain. The matching isolated duplicate fixture reproduces this independently of the currency/definition mismatch.

Observed output: the duplicate break says two current rows share the grain, but `source_refs` and `citation` contain only `/row/1`. Neither the other row reference nor the conflicting values are in the break. The artifact's top-level source list contains only the export-level reference. The packet can identify a duplicate group, but a reviewer cannot locate both conflicting rows from the packet's finding evidence without reopening the complete original input. Both output validators accept it.

Cause: `packages/actuarial-data-lineage-checker/scripts/calculate_or_transform.py:38-42` passes only `records[0]` to `brk`; `:26-32` supports that row plus one optional counterpart, not the duplicate group. Preserve the source references for every duplicate member, and preferably values/bases sufficient for the data owner to see the conflict. The calculation itself correctly selects no authoritative duplicate.

### D2 — Duplicate precedence suppresses the independent comparability finding (limitation)

The combined fixture reports only a duplicate. `calculate_or_transform.py:60-61` skips basis checks for every duplicate group, so the packet never states that every current record is USD/net/paid while the prior observation is EUR/gross/incurred. The isolated nonduplicate control proves the basis check works when reached. This is safe arithmetic behavior, since all movement remains withheld, but it is an incomplete reconciliation review if delivered without additional practitioner interpretation. Do not claim this packet identifies every independent data-quality problem. A future enhancement could report group-level basis conflicts without selecting a duplicate; this evaluation does not treat the absence of that enhancement as a fabricated numeric result.

## Boundaries of evidence

These are bounded synthetic practitioner-task simulations executed against local package snapshots. They test source-faithful calculation, missingness, comparability and review utility. They are not a security assessment, catastrophe-model scientific validation, source-authentication exercise, jurisdictional compliance conclusion, human professional acceptance or production-readiness certification. No human domain reviewer participated. Context and source assertions are explicitly synthetic. All artifacts preserve approval not_requested, execution not_performed and supplied_not_authenticated evidence assurance.
