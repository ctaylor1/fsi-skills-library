# Independent fresh forward evaluation: actuarial, reinsurance and finance cohort

Seven new practitioner requests and synthetic raw-source packets were constructed using only SKILL instructions and native reference contracts. Before any computation logic was inspected, raw sources, requests, native mappings and independent numerical expectations were frozen and hashed in `freeze_manifest.json`. No packaged tests, evals, fixtures, goldens, prior audits or other agents' outputs were read. No repository files were edited. No whole-package snapshots were made; code/reference files were hashed. No live legal, accounting, source authentication or qualified actuarial acceptance is claimed.

## Result

All seven bounded calculations match the independent arithmetic after three transparent interface-only mapping corrections. There are **98 passing numerical comparisons** plus **104 passing evidence/date/missingness/authority/control comparisons**. These are bounded assertions in seven cases, not 202 independent professional validations. Actual native commands total **30**, all exit 0: 21 original validate-input/calculate/validate-output calls, plus nine supplemental calls for three corrected mappings. A zero exit did not imply an evaluable result: three original outputs withheld native arithmetic because public contracts omitted executable input requirements.

All final outputs preserve supplied unresolved issues and are `needs-data`, completeness/evaluability `partial`. Known figures remain computable while source conflicts, unknown death identity/date, unapproved amendment, horizon completeness, unavailable liquidity evidence, unresolved wording, recognition judgment and conflicting controls remain open. No missing scalar was turned into zero; no hypothetical event or balancing journal was invented. This cohort tests narrative/source uncertainty alongside computable results; it does not exhaust nullable scalar branches.

| Case | Independent arithmetic checks | Key observed result |
|---|---:|---|
| Experience | 21 | 349 days, two deaths, expected 0.112328767, combined A/E 17.804878 |
| Pricing | 16 | PV net -11,498.351648; margin -59.182692% |
| Long-duration valuation | 9 | PV 990; two -10 bridge residuals; roll-forward ties at 1,060 |
| ALM | 17 | Base surplus 45.171050; funding gaps 70 base/89 stress; stress surplus -0.875296 |
| Assumed reinsurance | 18 | Active signed loss 75; expected loss 45; expected net 1; negative-cashflow probability 60% |
| Financial close | 9 | Balanced proposal; residuals +5/-5 remain |
| Capital | 8 | Available 170 vs 175 control; stress ratio 91.666667%; both available controls differ by -5 |

## Concrete defects discovered

1. **Experience native schema omits the exact exit enum.** Its `exit_reason` is documented as text; the method prose identifies death/first-lapse and “event exit.” The executable accepts only `event` or `censored`, while event_type accepts `death` or `lapse`. Original `experience/native_input.json` used death as the source-supported exit reason and produced risk_definition gaps. Supplemental `experience/mapped_v2/native_input.json` maps death to event without changing dates, count or study type.
2. **Reinsurance native schema omits exact supported capacity and term enums.** The required tokens are `context.capacity=assuming_reinsurer`, `trigger_basis=losses_occurring`, `loss_measure=ultimate_loss_including_lae` and `inuring_basis=net_of_scheduled_inuring` (latter two in terms and events). Original `reinsurance/native_input.json` used semantically equivalent human-readable labels and yielded capacity/unsupported_terms gaps. `mapped_v2` changes only aliases.
3. **Close native schema omits `data.profile.sign_convention`.** It documents the data-level debit-positive sign convention, but calculation additionally requires the same field in profile. The raw PROFILE already states the convention. Original `close/native_input.json` has a sign-convention gap; `mapped_v2` copies this existing fact to the required profile location.

These are interface documentation defects, not observed arithmetic errors. They were reported to the coordinating agent promptly for repository repair. Original inputs, expectations, command outcomes and output artifacts remain intact; mapped supplements have separate hashes and correction records. Limited domain.py enum/guard snippets were inspected only after the original freeze and native run. No expectation was derived from implementation output. Public method formulas were used to understand the stated job, while source quantities and expected calculations were authored independently.

## Evidence and limits

Every case folder contains request.md, raw_sources.json, mapping.md, native_input.json, independent_expectations.json, command logs with exact interpreter/script/argument/cwd/environment/exits, stdout/stderr, output.json, independent_check.json and practitioner_response.md. The three mapping corrections are isolated in mapped_v2, retaining initial results. `independent_check_summary.json` records counts, `post_review_package_hashes.json` records current hashes and any concurrent parent documentation edits, and `case_index.json` maps skill names to folders. Source_document equals the actual executed input in all final runs; frozen raw/native/request/expectation/mapping hashes are unchanged.

The methods are count-intensity studies, two-year deterministic survival-weighted cashflows, supplied liability-PV bridges, fixed-cashflow ALM, assumed no-reinstatement occurrence XOL, selected subledger/GL reconciliation and additive internal capital control ratios. No stochastic calibration, actuarial credibility, production data reconciliation, live-law validation, reserve determination, product approval, whole-company close certification or solvency certification was performed. The authored practitioner responses translate each observed result and open issue into a bounded reviewer disposition.
