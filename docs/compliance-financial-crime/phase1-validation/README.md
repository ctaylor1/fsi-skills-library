# Compliance & Financial Crime Phase 1 validation

**Implementation and bounded software verification passed on 2026-09-21.** Professional,
source, legal and deployment acceptance remain unestablished. Phase 2–4 workflows remain
planned. Package counts and tests are not a claim of a complete compliance program.

## Final checks

| Check | Result | Evidence |
| --- | --- | --- |
| Independent forward review | 49/49 expectations passed; all seven findings repaired | [review](forward-review.md) and [retained evidence](forward-evidence.tar.gz) |
| Whole-library structure | 332 packages; zero errors and warnings | [structure.log](structure.log) |
| Repository integration/regressions | 624 tests passed | [repository-tests.log](repository-tests.log) |
| Whole-library executable evaluations | 1900 passed; zero failed | [full-selftests.log](full-selftests.log) |
| Isolated portable packages | 16 packages; 85 command checks passed, including 394 focused test cases | [portable results](portable-results.json) |
| Legacy IDs, ownership and routes | All 15 original dispositions; six renamed IDs; privacy move; 27 declared routes; passed | [ownership.log](ownership.log) |
| Adjacent handoffs | Zero dangling references across 332 packages | [handoffs.log](handoffs.log) |
| Shared/pinned resources | CFC, Investment and Workflow checks passed | [integration checks](integration-checks.json) |
| Catalog regeneration | 332 rows, CSV parity, idempotent approved changes | [catalog check](catalog-check.json) |
| Change hygiene | Whole working-tree diff check passed | [diff-check.log](diff-check.log) |

These totals overlap: the focused suites are invoked by package evaluations, and package
evaluations also occur in the full-library run. Do not add them into a single unique-test
count. The affected packages retain 266 evaluation definitions; 181 nonexecutable
scenario/activation definitions were not run as model evaluations. The independent
forward pass adds fresh synthetic cases and separately recorded expectations.

## Independent review and corrections

[The forward review](forward-review.md) retains original inputs, outputs, commands and
source snapshots for seven initial failures: AML chronology, future SAR activity,
unsupported SAR rationale, conflicting exam approvals, future sanctions listing dates,
velocity equality and ledger-sensitive deduplication. Repairs were replayed on those
inputs. The original failures remain inspectable in the linked evidence archive.

A final API review added direct structural intake gates to the five crime calculators;
malformed or invalid input now stops calculation, while warning-only evidence gaps
remain partial. Sanctions direct ownership aggregation uses decimal arithmetic; fractional
interests totaling exactly 50% cannot fall below the threshold through floating-point
rounding. Focused tests cover exact/below-50% and exact/above-100% cases.

The 15 shared-contract regression tests use actual installed native producer and receiver
validators. Rehashed fabricated results, changed originals, missing mappings, changed
scope/audience, discarded evidence gaps and dropped source provenance are rejected.
Accepted handoffs still have no action authority. Common adapters exist for 11 schemas;
four explicitly remain native-only.

A separate read-only integration review found no material contradiction between the
installed methods, 27 route declarations, capability statuses and ownership documentation.
This is bounded review evidence, not professional acceptance.

## Reproduction and retained checkpoints

Use Python 3.10+; repository metadata validation additionally needs PyYAML. This run used
Python 3.14 and existing PyYAML 6.0.3 in a local validation environment. Native packages
use the standard library. Make `python` and `python3` resolve to that environment for
legacy whole-library evaluation commands; the affected CFC commands use `python3 -B`.

```sh
python3 -B tools/run_compliance_portable.py --output /tmp/cfc-portable-results.json
python3 -B -m unittest discover -s tools -p 'test_*.py' -v
python3 -B tools/run_selftests.py
python3 -B tools/validate_skills.py
python3 -B tools/check_handoffs.py
python3 -B tools/check_compliance_financial_crime.py
python3 -B tools/sync_cfc_resources.py --check
```

[The source snapshot](final-source-snapshot.json) records 6362 skill/shared/catalog/tool
files immediately before final checks. Readback confirmed no changes to those files
during verification. [Machine-readable summary](validation-summary.json) records exact
counts and acceptance limits. [Initial integration failures](initial-integration/README.md)
and `before-final-intake-*` logs preserve earlier checkpoints, not final evidence.

[Workspace preservation](workspace-preservation.json) records 12,493 unchanged other
baseline files, zero missing other baseline files and retained concurrent other-domain
deltas. The initial snapshot was taken after parallel work began and is not a clean
pre-task checkout. No reset/revert or attribution of concurrent work was inferred.
The external build-plan workbook remains unreconciled. No live action, commit, push,
merge or release was performed.
