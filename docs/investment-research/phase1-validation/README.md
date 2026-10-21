# Phase 1 validation evidence

Review date: 2026-10-20. Phase 1 implementation is complete within its documented
offline/native scope. Professional, institutional and deployment acceptance remain
not established. No live data service, entitlement, publication or execution was tested.

| Check | Observed result | Evidence |
|---|---|---|
| Whole-library regression suite, Python 3.12.14 | 973 tests passed | [Log](whole-library-unit-tests-python312.log) |
| Focused IR regression suite | 63 tests passed, with mutation/shape/arithmetic subcases | [Log](focused-unit-tests.log) |
| Isolated affected packages | 21 packages, 97 executable checks passed | [Report](portable-python312.json) |
| Specification/metadata/references | 372 skills; zero errors or warnings | [Log](skill-validation.log) |
| Catalog/handoffs/IR structure/AM migrations/index/resource pins | Passed | [Gate results](gates.json) |
| Saved-catalog regeneration | Byte-identical on repeat | [Gate results](gates.json) |
| Preservation of unrelated sources | No unexpected changes outside declared scope | [Audit](preservation.json) |

The independent expected-value suites are tools/test_ir_company_phase1.py,
tools/test_ir_models_phase1.py, tools/test_ir_credit_phase1.py and tools/test_ir_phase1.py.
They cover complete-output reconstruction, required originals, bad shapes, booleans,
nonfinite values, dates, unknown inputs and independently calculated numeric outcomes.
The portable runner rejects a traceback or missing dependency as negative-test evidence.
Query-only eval entries remain specifications unless explicitly exercised by an agent.

## Forward review and corrections

Independent agents used the SKILL/native-contract instructions to prepare fresh
synthetic requests. They did not receive intended outputs. Retained reproduction
artifacts are under [forward-review](forward-review). Earlier failing artifacts are
intentional evidence of findings, not current golden outputs.

| Finding | Correction and retained regression |
|---|---|
| Profile accepted boolean financial fact | Reject boolean/nonfinite financial facts; missing values withheld. |
| Debt seniority ignored negation | Qualified/negated seniority requires review. |
| Floating percentage spread lost | SOFR + 2.50% becomes 250 bps; incomplete index/spread requires review. |
| Future reported period accepted | Future observation needs an explicit forward-looking kind; reported facts withheld. Exact agent reproduction and forecast counterpart retested. |
| Claim-kind preparation unclear | Schema and error enumerate supported source/claim kinds. |
| Padded unknown basis accepted | Trim/case-normalize the unknown test. |
| Supplied contradiction resolution lost | Preserve permitted resolution lineage; claims remain contested pending human adjudication. |
| Same-sign root endpoints implied no roots | Report not-bracketed/unknown interior crossings; separate brackets recover roots at 100 and 300. |
| Duplicate sensitivity axes overwritten | Reject identical row and column drivers. |

These were agent engineering reviews, not independent financial-practitioner or
institutional sign-off. Additional forward cases confirmed the declared timing,
identity, rights, confidentiality, provider identity, bank-profile and action limits.

## Initial failures and environment limits

An initial portable run exposed eval commands using an unavailable python alias;
the seven affected packages now use python3 -B. The runner executes direct Python
entrypoints using its selected interpreter and strips PYTHONPATH/PYTHONHOME.

The host default Python is 3.9, below the declared 3.10+ package requirement. The
[initial whole-library run](initial-python39-unit-tests.log) recorded five failures:
two old credit regression inputs/expectations needed migration to the new strict
contract, and three unrelated cases depended on modern Python behavior (strict zip,
pairwise and floating summation). The credit tests now retain required instrument
identity and expect unknown source IDs to fail before calculation. The supported
Python 3.12 rerun passed all 973 tests; unrelated production code was preserved.

PyYAML was installed only into a temporary isolated validation environment. The
bundled Python used its pure-Python parser for repository specification checks.
The skill-creator quick validator has an older frontmatter allowlist that rejects
the repository's compatibility key. That key was retained; the repository validator
explicitly validates it and reports zero errors. No checker was weakened or bypassed.

## Reproduction and scope

Use Python 3.10+ (3.12.14 was used for the complete suite) and PyYAML for repository
frontmatter checks:

```sh
python3 -B tools/validate_skills.py
python3 -B tools/check_handoffs.py
python3 -B tools/check_investment_research.py
python3 -B tools/build_investment_research_index.py --check
python3 -B tools/sync_investment_resources.py --check
python3 -B tools/check_asset_management.py
python3 -B -m unittest discover -s tools -p 'test*.py'
python3 -B tools/run_investment_research_portable.py --report /tmp/ir-portable.json
python3 -B tools/check_investment_research_preservation.py docs/investment-research/phase1-validation/source-baseline.json
```

[Run manifest](run.json) pins package manifests, registry/helper sources, evidence
logs and the pre-edit baseline. Preservation compares source bytes, not Git cleanliness;
the initial checkout already contained substantial unrelated changes. Audited scope
includes the existing 18 IR packages, the two new packages, the shared normalizer,
two banker handoff references, discovery tooling, migration/approved catalog records,
affected manifests and documentation. The source workbook was not reloaded; repeat
saved-catalog generation is not proof of authoritative-workbook reconciliation.
