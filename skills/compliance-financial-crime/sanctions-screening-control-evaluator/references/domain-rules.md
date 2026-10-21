# Sanctions screening control rules

## Population, feeds and configured coverage

The supported population grain is a distinct screening-input-record ID. Customer counts, transaction values and event counts cannot be mixed. Each feed population is disjoint and falls inside the declared review population; received/screened IDs outside its population are malformed. Missing receipts, unscreened receipts and screened-without-receipt records are separate reconciliation findings. Each supplied feed must cover the exact review window and required fields/scripts. The union of feed populations must equal the declared population. These supplied arrays are review evidence; the helper cannot inspect actual data pipelines.

Configuration evidence declares the engine, engine/build version, configuration/version, vendor/reference/version, effective interval, fields/scripts, normalization, transliteration, matching method and threshold description. All must be source-bound and cover the review window. No default score, matching threshold, list or transliteration method is supplied. Engine execution and quantitative matching-score reproduction are unimplemented. Known tests must cite the same observed engine/build/configuration, list version and compatible feed input fields/scripts.

## Lists, time and requirements

The declared reviewed regimes must reconcile to supplied lists. Expected/loaded versions and entry IDs must agree. Publication and effective time must precede loading, and loading must precede the review window for a full-window coverage statement. Load/observation times must precede cutoff, assessment and receipt dates; foundation receipt granularity is one day. The update lag is **loaded_at minus effective_at**, compared to the supplied maximum seconds as exact decimal strings. A known update-lag breach is a supplied SLA failure, not missing list/version evidence: eligible detection observations remain measurable when the correct list/version/entries were effective and loaded before the review window. Missing update-lag requirements withhold the overall comparison while independently eligible detection counts survive. This package supports one supplied snapshot per declared list ID; changes within a window need a narrower review or separately reviewed adapter. It does not verify live-list completeness or legal effective-time sufficiency.

Explicit RFC3339 offsets are normalized to UTC for ordering. Local-time or naive timestamps are malformed. Knowledge cutoff is the foundation's date, so UTC dates are used conservatively. Missing times, limits, list evidence or source bindings withhold dependent coverage. Latency is supplied measured evidence, never a runtime benchmark; compare exact supplied seconds against an exact supplied maximum. Missing latency/requirements withhold the overall comparison while independently eligible detection observations can still contribute to sample counts.

## Labels, testsets and measured outcomes

A testset declares exact case IDs, version, label reference/version/scope, label known-at instant, represented dimensions, sampling method and supplied acceptance for measurement. Labels are expected **alert behavior on the scoped test case**, not universal sanctioned-person status or legal ground truth. The label reference and expected detection must use distinct source records from engine outcome/time/latency/version observations. Exact source separation is a necessary consistency check; it cannot authenticate independence. Expected labels must bind to the testset label-reference sources. Labels dated after their observations, unknown labels, unaccepted/out-of-version tests, errored observations and incomplete engine workpapers remain unmeasured.

One observation per testset/case identity avoids double-counting repeated runs. Multiple runs require separately scoped case identities. Required challenge dimensions are institution supplied; the helper reports unmeasured cases and uncovered dimensions. Missing cases or untested dimensions do not become negatives. Convenience or targeted testsets provide observed sample outcomes only and support no statistical population inference.

| Expected test label | Eligible observed outcome | Measured sample class |
| --- | --- | --- |
| expected-alert | alert | true_positive |
| expected-alert | no-alert | false_negative |
| expected-no-alert | alert | false_positive |
| expected-no-alert | no-alert | true_negative |
| unknown or unsupported | any outcome | unmeasured |
| any label | error, unknown or incomplete | unmeasured |

False-positive rate = FP / (FP + TN); false-negative rate = FN / (FN + TP). Output stores integer numerator, denominator and exact fraction, with null fraction when the denominator is zero. Criteria comparisons use exact rational arithmetic converted from decimal strings, so arbitrarily fine supplied precision is preserved. Unlabeled observation counts, all engine outcome counts and ineligible measurement counts are distinct from measured confusion counts.

## Controls and professional meaning

Supported control dimensions are population, feed, list, field, transliteration, matching, configuration, vendor, resilience and latency. Each supplied workpaper binds the requirement, procedure, exact review population, observation time, outcome, evidence completeness and finding. A full observed failure establishes observed coverage but fails the supplied review criteria. An unknown/incomplete workpaper establishes neither a pass nor completed coverage. Operational QA, second-line monitoring and independent testing mandates remain separate; no assurance opinion is issued.

The overall supplied-review comparison is null unless review scope, feeds, lists, configuration, known-test coverage, latency evidence, all control dimensions and both sample denominators/criteria are complete. If complete, known failures, list-update lag or latency breaches, or measured sample criteria breaches yield false. Complete observed evidence may still fail supplied criteria. Neither true nor false determines operational effectiveness, legal exposure, person identity, independent assurance, approval or remediation closure. Foundation issues and all substantive gaps remain in the draft.
