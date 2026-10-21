# Phase 3 validation evidence

Completed 2026-10-20 for the bounded supplied-evidence library scope. Professional,
institutional and production acceptance remain not established. Test inventories
overlap; these counts are not additive.

| Check | Final observed result | Evidence |
|---|---|---|
| Whole repository regression suite, Python 3.12.14 | 1,184 tests passed | [Log](whole-library-tests.log) |
| Focused IR regressions | 274 tests passed | [Log](focused-tests.log) |
| Standalone affected packages | 39 packages, 257 command checks passed | [Report](portable.json) |
| Specification, metadata and references | 390 packages, zero errors/warnings | [Log](skill-validation.log) |
| Structure, aliases, indexes, handoffs, AM boundaries and resource pins | Passed | [Gates](gates.json) |
| Saved-catalog regeneration | Byte-identical | [Record](catalog-repeat.json) |
| Source-byte preservation | No unexpected changes; prior phase evidence untouched | [Audit](preservation.json) |
| Independent fresh forward review | All final cases passed; exact artifacts retained | [Copies](forward-review), [copy readback](forward-review/copy-readback.json) |

The final portfolio has 37 installed IR target packages and five planned Phase 4
capabilities. Three Phase 3 packages and three new mappings bring the reviewed
adapter inventory to eight. Portable verification includes the two shared owners
alongside the 37 IR packages; it strips inherited Python paths and runs outside
the repository. Separately installed methods remain explicit adapter dependencies.

## Independent behavior and findings

Separate agents read the authored instructions and built fresh synthetic cases
without receiving intended numerical answers. Reviews cover all three new methods,
actual native model candidates and producer/receiver reconstruction, plus an isolated
router's bundled handoff entrypoint. Evaluated source hashes and exact originals,
results and transcripts accompany each retained report.

- [Event review](forward-review/quality-agent-events/report.md): ten fresh positive/adverse cases, including independent repurchase and refinancing arithmetic.
- [Model-update review](forward-review/events-agent-updates/report.json): fresh operating/DCF revisions and snapshot advancement, with immutable originals, independent valuation and adverse variants.
- [QA and adapter review](forward-review/updates-agent-quality-adapters/review.md): twelve fresh quality cases and ten actual adapter/portability cases, including inherited issues, conflicting receivers, package tampering and unpinned code.
- [Final control replay](forward-review/quality-agent-events/final-snapshot-and-acquisition-review/corrected-native-intake/report.md): acquisition funding timing, legitimate snapshot advancement and rejection of historical lookahead despite internally consistent hashes.

Two controls were strengthened during review. First, acquired cash and retained
proceeds could leave nonnegative closing cash while hiding an upfront cash gap;
separate upfront and ending requirements now retain that gap and propagate it into
blocked QA readiness. The replay closes with cash 10 but correctly reports an
unestablished upfront requirement of 20. Second, current-date eligibility could
otherwise rehabilitate an original containing later-known evidence; the updater
now requires eligibility under the original context and requests rebasing/adjudication.

Initial harness failures are retained separately: the first adapter expectation
incorrectly discounted terminal value at midyear, an output-reader test omitted its
required original flag, and a route test used the wrong adapter ID key. Those tests
were corrected against the actual documented contracts. Native model code was not
changed to accommodate expectations. One independent replay initially used an
unsupported discounting enum; its error and corrected native intake are both saved.
Superseded manifest-drift observations arose while authors were still editing;
final native, manifest and isolated-entrypoint checks used the frozen packages.
[integration-whole-library-tests.log](integration-whole-library-tests.log) records
an earlier passing run; whole-library-tests.log is the final 1,184-test run.

## Scope of the checks

New tests independently verify cash/debt/share, valuation and arithmetic identities;
version/prior-value conflicts; required-update and review coverage; date advancement,
old/current source cutoffs, permissions and identity; missingness and financial basis;
full output mutations/deletions/additions; strict duplicate/nonfinite JSON readers;
and actual public command execution. An invalid financial candidate may be staged
with native_validation explicitly not-performed, but cannot pass its reviewed native
model adapter. No supplied pass flag substitutes for actual receiver execution.

Source hashes and reconstruction establish correspondence to supplied input. They
do not authenticate a filing, entitlement, current model store or source truth.
QA verifies declared structured checks; source-text entailment, economic semantics,
full research coverage and risk/disclosure meaning still need human assessment.
Supplied resolved contradictions and judgment findings are not automatically closed.
A reviewed native handoff never grants model, publication, trading or live-write
approval. No live financial or system-of-record action was performed.

The generic skill-creator quick validator rejects the supported compatibility
frontmatter key through its stale allowlist; [exact results](skill-creator-compatibility.json)
are retained. The repository validator explicitly validates that field and passed
all 390 packages. No metadata was removed or checker weakened. Analytical packages
need only Python 3.10+; full tests ran on 3.12.14. PyYAML was used from the existing
temporary isolated validation environment, without a repository/global install.

## Reproduction and preservation

```sh
python3 -B tools/validate_skills.py
python3 -B tools/check_handoffs.py
python3 -B tools/check_investment_research.py
python3 -B tools/build_investment_research_index.py --check
python3 -B tools/sync_investment_resources.py --check
python3 -B tools/check_asset_management.py
python3 -B -m unittest discover -s tools -p 'test_ir*.py'
python3 -B -m unittest discover -s tools -p 'test*.py'
python3 -B tools/run_investment_research_portable.py --report /tmp/ir-phase3-portable.json
python3 -B tools/check_ir_phase3_preservation.py docs/investment-research/phase3-validation/source-baseline.json
```

The pre-edit baseline contains 18,625 source-file digests. Existing analytical
engines and fixtures, unrelated packages and prior Phase 1/2 validation evidence
are unchanged. Existing IR/shared packages receive only the reviewed canonical
evidence reference and its manifest pin. The initially dirty Git state is retained
in the baseline; aggregate Git differences are not attributed to this phase.
Repeat local catalog generation proves reproducibility with approved additions and
overrides; the external authoritative workbook was not reloaded.

The [run manifest](run.json) pins actual package manifests, current changed sources,
registries and retained evidence. Saved artifacts and copied forward-review files
were read back and checked against their recorded hashes. This is software and
supplied-artifact evidence, separate from practitioner/institutional sign-off.
