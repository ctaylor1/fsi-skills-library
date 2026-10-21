# Evidence reconciliation validation

Completed 2026-10-20 for the four supplied-evidence reconciliation gaps retained
by the previous repair review. [Implementation and migration](../evidence-reconciliation-implementation.md)
describe issuer credit 0.2.0 and surveillance 0.4.0. Earlier reports remain attached
to their original source versions and were not rewritten.

| Check | Final observed result | Evidence |
|---|---|---|
| Full repository suite, Python 3.12.14 | 1,379 tests passed | [Log](whole-library-tests.log), [command](whole-commands.json) |
| Focused Investment Research suite | 469 tests passed | [Log](focused-tests.log), [commands](focused-commands.json) |
| New regression methods | 55 passed: issuer 30, surveillance 25 | [Issuer tests](../../../tools/test_ir_issuer_evidence_reconciliation.py), [surveillance tests](../../../tools/test_ir_surveillance_evidence_reconciliation.py) |
| Isolated standalone packages | 44 packages, 299 declared command checks passed, zero errors | [Report](portable.json) |
| Metadata, specification and references | 395 packages, zero errors and warnings | [Log](skills.log) |
| Native ownership/profile/subject structure and current indexes | Passed | [Structure](structure.log), [index](index.log) |
| Portable resources and package manifests | Passed | [Log](resources.log) |
| Catalog regeneration | JSON and CSV byte identical after isolated `--from-current` rebuild | [Proof](catalog-rebuild.json) |
| Real public-command replays | Four previous-version gaps reproduced; ten repaired cases passed, including four byte-identical legacy originals | [Before](before-reconciliation/report.json), [after](after-reconciliation/report.json) |
| Independent skill use | 20 fresh intake cases, 138 declared checks, four altered-output rejections; zero check failures | [Review and draft](forward-review/INDEPENDENT_CREDIT_REVIEW.md), [assertions](forward-review/assertion_results.json) |
| Preservation | 956 earlier phase files and 524 earlier repair files unchanged; no changes outside declared ownership | [Audit](preservation.json), [baseline](source-baseline.json) |

These inventories overlap: the 55 new methods are included in both test suites.
Portable commands, fresh cases, native probe cases and independent assertions are
different inventories and are not additive. Commands use supplied synthetic data;
none establishes real source authenticity, completeness or practitioner acceptance.

## What changed and how it was challenged

Issuer regressions independently check signed arithmetic, distinct equal-valued
events, total/component additivity, row and canonical-event aliases across sources,
conflicting versions/citations/blocks, missing identity, issuer/perimeter/period
scope, included/excluded instruments, nullable principal, currency/unit/basis
mismatches, exact carrying-value bridges and source eligibility. Exact decimal
tieouts accept 0.1 + 0.2 = 0.3 and reject a nearby mismatch without a tolerance.
Missing adjustment proof withholds adjusted metrics; missing debt proof withholds
debt-dependent ratios while retaining independently supported results.

Quote regressions exercise requested security/issuer and currency mappings,
effective periods covering both observations, missing/duplicate/conflicting
records, wrong source roles, values, times, versions, registered blocks and
citations. They also retain the previous timing, cutoff, rights, current-age,
economic as-of, exact-boundary and detached-original controls. Selected evidence
drives the calculation; unrelated unused records cannot contribute numerical
values or successful reconciliation context.

Three existing test files were updated to isolate their original controls using
the new evidence contracts: issuer adjustment/source-vintage cases, surveillance
time/freshness cases and routing's actual security identity. Their prior versions
are preserved, with all other active IR tests, in `pre-edit/tools/`. Assertions
were retained, including independently specified 107 adjusted EBITDA and its
leverage/coverage ratios for the separate signed-reversal case.

## Before/after public-command proof

The [pre-edit snapshot manifest](pre-edit-manifest.json) covers 92 files: the two
previous packages, active IR tests and source bytes referenced by the earlier
repair run. Each snapshot digest matches the new pre-edit baseline; the earlier
repair's recorded source hashes also match the corresponding retained bytes.

[Prior-gap reproduction](reproduce_prior_gaps.py) runs the actual prior-version
input, calculation and output commands against those copies. It records formerly
complete outputs for a repeated economic cost under another row ID, EUR 700
instrument principal beside USD 400 reported debt, an unrelated quote security and
financial-statement quote sources.

[Repaired replay](replay_reconciliation.py) uses the current public commands and
checks all computable outputs against detached originals. The four legacy inputs
are byte identical to their before versions and now remain partial with dependent
measures unavailable. Six populated-evidence cases additionally show that valid
math remains available while duplicate costs, incompatible debt, unrelated
securities and unsupported quote source kinds trigger their specific controls.
No previous golden or report was changed to create this before/after result.

## Independent fresh-case review

A separate agent read the published skills and schemas, saved raw facts and
independent rational expectations before execution, and froze both packages.
Fixture input envelopes were used only to learn structure; expected goldens were
not used. The review authored two fresh baselines plus 18 adverse/boundary intake
cases. Eighteen computed outputs reconstructed against separately retained
read-only originals; two malformed cases rejected with controlled errors.
Four changed outputs also rejected. All 138 declared arithmetic/control/hash
assertions passed.

The independent data produces a +8 adjustment from components +7/+5 and a separate
−4 event, adjusted EBITDA 92, and debt 450 principal −12 carrying-value bridge =
438. Reported and adjusted gross leverage are 438/84 and 438/92. The selected OAS
observations produce +42.5 bps, with a three-hour current age under an eight-hour
policy. Exactly eight hours remains eligible; one second beyond it withholds the
comparison. The draft distinguishes nine-month denominators from annual/LTM
measures and makes no rating, covenant, approval or trading claim.

The [readback proof](forward-review/readback_verification.json) records 217 indexed
files, 133 reopened JSON documents and live/frozen package agreement. The complete
219-file directory, including its index and verification record, was copied and
read back byte equal here. Exact commands and original scratch paths remain in
[execution records](forward-review/execution_records.json); source snapshots and
all raw cases are retained alongside the draft. The independent harness's initial
stdout-only assumption was corrected to inspect stderr as well; this changed no
native result or package and is disclosed in the review.

## Preservation and remaining boundaries

The new baseline captures 19,932 files in the initially dirty checkout. The
preservation guard compares those bytes rather than attributing the aggregate Git
diff. All earlier Phase 1–4 implementation/validation and control-repair records
are protected. The earlier repair's 522 indexed evidence hashes were also
rechecked. Current changes are restricted to the two packages, necessary existing
and new regression tests, package-version catalog entries, current documentation
and this new checkpoint. Shared resources, routing registries, aliases, reviewed
adapters and Phase 1 surveillance fixtures are unchanged.

The [run record](run.json) binds exact commands, interpreter, package manifests,
source hashes, artifact hashes and readback. Saved-catalog regeneration verifies
local reproducibility only; the external authoritative workbook was not reconciled.

The installed external skill-creator quick validator still rejects existing
`compatibility` metadata. Its [raw results](skill-creator-quick-validation.json)
are retained; the repository validator explicitly supports that field and passes
all 395 packages. Supported metadata and the external validator were not altered.

The four recorded software reconciliation gaps are addressed within explicit
supplied-evidence contracts. Real economic identities, extraction completeness,
document contents and permissions remain supplied assertions. Renaming both a
canonical identity and its purported evidence cannot authenticate a real event.
Live source authentication, independent accounting/legal/practitioner acceptance,
institutional deployment and publication or execution authority remain separate.
