# Phase 1 validation — 2026-09-20

Phase 1 implementation and bounded technical verification are complete. All final
checks below passed against the current feature-branch working tree. These checks
do not establish source truth, professional acceptance or production readiness.

| Check | Final result | Evidence |
|---|---|---|
| Whole-library package evaluations | 1,605 passed; zero failed | [Command log](library-selftests.log) |
| Repository regression methods | 497 passed, including 120 AM Phase 1 methods | [Test log](repository-tests.log) |
| Isolated package installations | 54 affected packages; 289 declared checks passed | [Full results](portable-results.json) |
| Real producer/receiver integration | Seven tests passed, including actual artifact/handoff CLIs | [Integration log](native-handoff-integration.log) |
| Skill structure | 302 packages; zero errors or warnings | [Validation summary](validation-summary.json) |
| Catalog, ownership, routes and aliases | All 30 AM dispositions and 55 migration records resolve; no dangling handoffs | [Validation summary](validation-summary.json) |
| Resources and regeneration | Pinned bundles match; catalog regeneration is byte-for-byte idempotent | [Validation summary](validation-summary.json) |
| Independent investment cases | Nine cases, 29 expected assertions passed under final helper | [Final replay](investment-final-replay.json), [original evidence](investment-forward-review.json) |
| Independent operations cases | Five scenario groups pass after two recorded precision repairs; eight unsupported-bound probes reject | [Original failures and repaired replay](operations-forward-review.json) |

These counts overlap. Portable checks rerun package evaluations, and the seven native
integration tests are included in the 497 repository methods. They are not additive
independent model or practitioner evaluations. Router checks include 144 variants
over 24 declared intents; they test deterministic routing, not natural-language
activation accuracy in every agent host.

## Findings retained and repaired

- [Operations forward review](operations-forward-review.md) records two cases where
  default Decimal precision lost a real quantity difference while reconstruction
  still passed. Both methods now use isolated precision-256 arithmetic with rounding
  traps and declared input bounds. Original failures remain intact, with separate
  repaired outputs and boundary-rejection evidence.
- [Contract findings](contract-findings.md) records a fabricated factsheet field that
  passed the earlier envelope checks after hashes were recomputed. Handoff acceptance
  now requires the detached source request and actual producer output reconstruction,
  followed by real receiver validation. Envelope-only inspection is explicit and
  insufficient for handoff acceptance.
- The same finding record documents raw-original injection into a native factsheet.
  Native validators now reject embedded `source_input`, even when it matches the
  detached original. Restricted original data cannot re-enter through that field.
- Contract tests also cover authoritative identity/date paths, issue propagation,
  false completeness, malformed JSON types, future evidence, source restrictions,
  changed scopes, unmapped fields and unsupported method origins.

The [investment review](investment-forward-review.md) preserves its original evidence
byte-for-byte. Its final replay explicitly records the later shared-helper digest
change and rechecks the same expected arithmetic and negative cases.

## Reproduction

Use Python 3.10+ with PyYAML for repository metadata validation. The package evaluation
commands use both `python` and `python3`; activate the same virtual environment before
running them. The verification run used a temporary environment with PyYAML 6.0.3.
An initial run without a `python` executable failed at command launch; that was an
environment setup failure, not a native method result. Final logs above use the
correct interpreter environment.

```bash
python tools/validate_skills.py
python tools/check_handoffs.py
python tools/check_asset_management.py
python tools/build_asset_management_index.py --check
python tools/sync_investment_resources.py --check
python tools/run_selftests.py
python -B -m unittest discover -s tools -p 'test_*.py'
python tools/run_asset_management_portable.py --output /tmp/investment-portable-results.json
```

Catalog regeneration was checked with `tools/build_catalog_from_xlsx.py --from-current`.
No external workbook was edited. Existing workflow, insurance, payment and wealth
resource checks all passed. Protected pre-existing Insurance files and catalog
overrides/additions are preserved. Affected-package Python and JSON syntax checks,
local Markdown links and Git whitespace checks passed.

## Acceptance still required

Six native schemas intentionally cannot use common investment envelopes; see the
[contract guide](../CONTRACTS-AND-PACKAGING.md). Other mappings remain explicit rather
than inferred. Supplied source rights, method labels and reviewer identities are not
authenticated. The current common native adapters accept only local-analysis origin.
Engine interfaces do not constitute installed or accepted engines.

Independent institutional benchmarks, realistic licensed datasets, broader host/model
evaluations, specialist review, jurisdiction maintenance, authenticated access and
operational deployment gates remain open. The tests do not certify all AM workflows,
all instrument types, every disclosure or a generally effective information barrier.
Phases 2–4 remain planned in the [implementation plan](../IMPLEMENTATION-PLAN.md).
