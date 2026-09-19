# Insurance claims independent forward evaluation and bounded repairs

Date: 2026-09-18. All data are invented, offline examples; no customer records or external actions were used.

## Method and independence

The evaluator first read the actual four final SKILL.md files, domain rules and native calculator/input/output interfaces. The four requests and practitioner acceptance criteria were frozen in `scenario-design-frozen.json` before inspecting existing tests, eval specifications or golden fixtures. Original requests, native inputs, stdout, stderr, command exit codes and pre-run source hashes remain at the root of this directory. Source copies for the two repaired packages were saved under `source-before/`.

After reporting defects, the same evaluator received bounded implementation ownership for claims-triage-assistant and subrogation-opportunity-screener, read their existing tests, implemented the repairs and replayed the unchanged native inputs under `after/`. This is an independent initial forward evaluation followed by author verification, not an independent second post-fix review. No shared helper or other package was edited. The exact repair file list is `after/owned-repair-files.json`.

## Outcomes

| Request | Original result | Final replay |
|---|---|---|
| Urgent liability claim with liability/exposure unknown | U1 score 10, S1 score 12 provisional, overdue by one day, seven review routes; generated no-fraud/at-fault wording defect | Same priorities and uncertainty; neutral fraud/recovery referral wording; native validators pass |
| Quoted fault assertion plus contrary and missing evidence | One contested, one contradicted, one unsupported; quote retained; rehashed generated liability conclusion rejected | Same evidence result and native validators pass |
| Unknown waiver/prior recovery and missing deductible/financial source | Review, unknown availability, null calculated economics, time-critical diary | Same outcome; no financial recovery signal fires |
| Receipt with missing inventory/form/amount | Receipt recorded, normalization complete, completeness gaps, timeliness checked; receipt not blocked | Same outcome; native validators pass |
| Explicit-null money boundary variant | Input rejected with two errors and calculator raised ValueError; no output artifact | Input accepted with unknown warnings; Review with null calculated economics and preserved nonfinancial signals |

All five final native inputs pass the actual input validator, calculator, output validator and `validate_artifact(..., input_doc=..., output=...)` source-binding checks. Four final router requests pass route validation using the live inventory of 23 final insurance packages: rate adequacy, P&C claimant appeal and portfolio fraud discovery remain capability gaps; treaty comparison routes to reinsurance-contract-reviewer.

## Repairs

1. Subrogation input validation accepts explicitly null paid/deductible values as factual unknowns while rejecting malformed non-null values. Paid amount remains a required nullable field. The existing calculator preserves null economics and Review. Output validation now also rejects rehashed zero financial values or fired financial signals when economics is not evaluable.
2. Generated triage routing language no longer implies fraud was ruled out or third-party fault established. Focused tests preserve urgent human and specialist recommendations and reject resealed copies of the two unsupported phrases.
3. Narrow domain rules document these boundaries. Only owned existing valid goldens were regenerated. No changes were made to shared helpers.

## Verification

- Claims triage focused tests: 8 passed.
- Subrogation focused tests: 10 passed, including individual/both null amounts, 16 malformed non-null amount subcases, and resealed-zero rejection.
- Owned executable evaluation commands: 12 passed, 0 failed.
- Repository structural validator: 2 packages, 0 errors, 0 warnings.
- Scoped Ruff F/E9: passed.
- Unchanged-input final domain/calculation/source-binding runs: 20 commands passed (five inputs times four stages).
- Final installed-inventory route replay/validation: 8 commands passed (four requests times two stages).
- Generic skill-creator quick_validate rejects existing `compatibility` frontmatter in both packages, while the repository validator explicitly supports it. This schema mismatch was not changed.
- Broader strict Ruff has 25 pre-existing diagnostics before and after, zero introduced; it is not a clean full-style result. No baseline cleanup was performed.

Full commands, return codes and raw results are in `execution-manifest.json` and `after/execution-manifest.json`. Final acceptance review is in `after/acceptance-review.json`; request-specific practitioner responses are saved beside original and final outputs. `after/native-input-hashes.json` identifies the exact unchanged inputs; pre/post source hash files identify evaluated revisions.

## Limits

The natural-language requests were interpreted and mapped to native JSON by this evaluator; the calculators do not classify free-text requests or authenticate quoted passages. The supplied synthetic rules, sources, proportions and diary dates are not verified legal, operational or actuarial standards. Some lower-level source references remain synthetic labels without a separately authenticated source document. Envelope hashes establish content binding, not truth or professional adequacy. The regex conclusion checks are bounded, not a comprehensive semantic guardrail. No actual receiver handoff, system assignment, source-system integration, human adjuster review or production action was performed. Passing deterministic agreement and these forward examples do not demonstrate practitioner acceptance or production readiness.
