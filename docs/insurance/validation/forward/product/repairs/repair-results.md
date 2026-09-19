# Bounded insurance product repairs — 2026-09-18

Completed changes are limited to `premium-quote-comparator`, `reinsurance-contract-reviewer`, and `pc-reserving-analysis-assistant`. The original forward-test snapshot is unchanged. The original failure inputs were replayed without changing a byte; hashes and native input/calculation/output validator logs are in `before/` and `after/`. No shared `insurance_contract.py`, catalog or root files were changed.

## Repair results

| Reproduction | Before current-code repair | After | Validation |
| --- | --- | --- | --- |
| Quotes with both building limits null and numeric deductibles | Comparable, B ranked, 100 spread, complete | `coverage_unknown`, not comparable, null ranking/spread, partial; individual premiums retained | Input, calculation, output all exit 0 |
| Zero base premium with one contractual reinstatement | Restored 0, charge 0 | Restored 7m, charge 0; ceded 7m and remaining aggregate 13m unchanged | Input, calculation, output all exit 0 |
| Missing large-loss schedule | Original forward snapshot asserted zero; root's fix was already present in the current-code before run | Root fix confirmed: `not_evaluable`, null count/total/flag, partial artifact | Unchanged reproduction input; all stages exit 0 |

The quote correction also handles an omitted/empty limit and an omitted/null deductible, preserving the distinction between unknown and an explicit zero deductible. Regression checks retain normal comparability for supplied equivalent terms. The zero-premium test checks restoration across successive losses (7m then 3m, capped at the contractual 10m reinstatement capacity), verifies zero charges, and confirms the output validator rejects a rehashed incorrect restored amount.

The reserve output template now uses `Paid` / `Total unpaid` for paid triangles and `Reported incurred` / `IBNR` for incurred triangles. Severity and frequency denominators are labeled supplied claim counts, with count basis and compatibility made explicit. Supporting data gaps no longer force the template to imply a failed triangle indication, and unavailable large-loss data is shown as unknown rather than zero. The template labels method-indicated sensitivity consistently. H1 titles now read `P&C Reserving Analysis` and `Reinsurance Contract Review`.

The reinsurance golden-task prose incorrectly attributed the first 7m restoration to occurrence O-2; it now attributes 7m/1.4m to O-1 and the remaining 3m/0.6m to O-2. Existing positive golden JSON files were regenerated from the current engines and retained their valid narratives and clause summaries. Their output bytes are unchanged because these ordinary positive fixtures are not affected by the new edge-case corrections.

## Checks and replay

Nineteen package unit tests passed (6 quote, 7 reinsurance, 6 reserve), including four added test methods and five missing-dimension subcases. The new defect tests were run before the code change and failed as expected; those logs are preserved. All native deterministic and negative-output evaluation commands in these three package manifests returned their expected exit codes and messages. Ruff E9/F passed for all three script directories after removing unused imports and the unused reinsurance aggregate variable. The repository skill validator reports 3 skills, 0 errors, 0 warnings.

Exact command arrays, working directories, expected/actual exit codes and stdout/stderr paths are in `verification-log.json` and each reproduction's `run-log.json`. Main commands used:

- `/tmp/fsi-p0-venv/bin/python -B /tmp/insurance-product-forward-20260918/repairs/replay.py before` and `after` (the before run is preserved; running it again would capture the current repaired state).
- `/tmp/fsi-p0-venv/bin/python -B skills/insurance/<package>/scripts/test_phase1.py` for each owned package.
- Native input, transformation, output and negative-output commands declared in each package's `evals/evals.json`.
- `/tmp/fsi-p0-venv/bin/ruff check --select E9,F skills/insurance/<package>/scripts`.
- `/tmp/fsi-p0-venv/bin/python -B tools/validate_skills.py skills/insurance/premium-quote-comparator skills/insurance/reinsurance-contract-reviewer skills/insurance/pc-reserving-analysis-assistant`.

The generic skill-creator quick validator was also run and failed for all three packages because its allowed frontmatter field list omits the repository's preexisting `compatibility` field. That limitation is recorded as a failed generic check, not silently counted as a pass. The existing field was preserved; the repository's validator explicitly supports it and passed.

## Bounded limits

This verifies the observed synthetic defects, the owned packages' existing executable evaluations and the template wording. It does not establish professional actuarial/contract interpretation acceptance, live source completeness, production connector behavior or broad insurance product coverage. A sourced empty large-loss schedule remains distinct from an unavailable schedule under the root's current implementation. All approvals and external actions remain unperformed.
