# Independent forward governance evaluation — initial results

**Status: PARTIAL — initial forward defects preserved; package repairs belong to root.**

Twenty fresh synthetic practitioner cases cover eleven native methods: horizon scan/applicability, program design/traceability/risk/change/effectiveness, sanctions exposure, information sharing, typed non-SAR reporting and notification. The first eighteen were run against the then-current package code with no hash changes during execution. Two subsequent evidence-conflict/expiry cases used the frozen initial risk code whose executable hashes exactly match the pre-run package hashes. No shipped fixture/golden file, implementation-agent notes or previous test outcomes supplied the scenarios or expected conclusions. Pre-run input and expectation files were saved before calculating.

## Counts and bounded conclusions

- Initial eighteen cases: input validation **18/18**, calculation **18/18**, detached output validation **18/18**; **54/54** native CLI exits successful.
- Supplementary evidence cases: input validation **2/2**, calculation **2/2**, detached output validation **2/2**; **6/6** exits successful. Combined **60/60** command exits are pipeline success, not substantive acceptance.
- Explicit expectation checks: **147/150 pass**, **3/150 fail**, across all twenty cases. Three failed checks represent **two native notification defects** (immediate priority and row-order dependence).
- Original notification failure replay: **3/3** byte-for-byte reproduction through preserved original executable snapshots.
- Initial companion input schema audit: **8/8** casework inputs accepted by native CLI are incompatible with the literal advertised string-only source-fact value type in **4** JSON input schemas. This is a contract contradiction, recorded separately from the 150 expectation checks. This was a direct literal-type/path audit, not a full external JSON Schema validation; jsonschema was unavailable in this evaluator runtime.
- One evaluator oracle wording defect is explicitly preserved: pre-run case12 arithmetic was incorrectly rounded to 50 by Python's default Decimal context. The input stakes, second pre-run expectation, native result and independent exact Fraction oracle support **49.9999999999999999999999999999**, strictly below 50. This is an evaluator error and is not a package failure. The 147/150 score uses the corrected exact oracle with this limitation declared.

## Reproduction findings

1. **Immediate duty loses urgent review.** Case16 entity/activity and materiality are true, sourced timing is immediate and chronology/channel are supported. Unknown due date causes review_state=unknown instead of urgent-human-notification-review. The only native gap is the unnecessary fixed-date evidence requirement. Initial domain code evaluated due_date through the same compulsory claim path as fixed-date obligations.
2. **Unrelated prior obligation changes a supported row.** Cases17/18 contain the same two obligations in opposite order. N-GAP has a missing channel. Supported N-FIXED is unknown when second, draft-for-human-notification-review when first. The domain loop accumulates row gaps into global issues and then uses those accumulated issues for later row state decisions.
3. **Advertised fact schema cannot carry required native evidence.** Initial sources[].facts[].value is string-only in sanctions, information-sharing, typed-reporting and notification schema files. Necessary method approval and scope objects, blocked/eligibility booleans and similar native facts cannot satisfy that schema. Exact source-value consistency forbids replacing those values with string lookalikes. See schema-fact-type-audit.json for exact pointers and original file hashes.

## Evidence and professional usefulness

The supporting practitioner draft provides substantive source-located observations, actual dates, denominators, exact direct ownership/currency calculations, ownership/permission/population gaps, specific owner questions, and proposed next steps. It keeps native artifacts unchanged and distinguishes evaluator recommendations from native observations. Notification prioritization cannot be accepted as initially shipped. The other sampled methods preserved the tested scope/unknown/evidence/date/calculation boundaries, including null residual for testing gaps, no mapping assurance, no activity-based favorable effectiveness, no pilot-to-full-release reuse, no indirect sanctions default, withholding SAR existence/unnecessary data and no mixed-currency FX.

## Limits

All institutional/legal rules and source packs are synthetic, supplied and unverified. This is a bounded forward workflow evaluation of extracted JSON and manual practitioner synthesis, not an independent raw-document extraction benchmark, representative operational dataset, model quality assessment, source-authenticity check, legal/professional acceptance, actual independent assurance or deployment readiness review. No live acquisition, scheduling, filing, send, launch, account/system change, external message, commit or receiver workflow was executed. Current root repairs/rechecks are outside these preserved initial-result counts. No package, shared module or catalog was edited by this evaluator.

## Saved artifacts

- pre-run-expectations.md and individual expectations.json: original raw facts/requests and pre-calculation expectations.
- pre-run-package-hashes.json, initial-code-hashes.json and initial-code/: original instruction/script hashes and 66 frozen executable files; original casework schema snapshots were captured where their hashes still matched.
- initial-runs.json and supplementary-runs.json: exact commands, return codes, input/output/expectation hashes and stdout/stderr locations.
- Per case: input.json, initial-output.json, CLI stdout/stderr, initial-run.json; notification replays remain separately named.
- failure-replay.json: reproducible original notification artifacts and hashes.
- expectation-score.json: all 150 concrete checks and observed values.
- schema-fact-type-audit.json: initial advertised schema contradiction with exact input/schema pointers.
- evaluator-correction.md and exact-boundary-oracle.json: transparent evaluator arithmetic correction.
- practitioner-review.md: substantive professional draft outside exact native results.

Every original failure remains retained for root replay and post-repair comparisons. No original input, expected text or output was silently corrected.
