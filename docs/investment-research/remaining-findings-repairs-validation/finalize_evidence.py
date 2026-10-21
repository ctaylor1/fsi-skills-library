#!/usr/bin/env python3
"""Finalize this repair's bounded evidence after all declared checks finish."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def main():
    commands = read(HERE / 'whole-commands.json') + read(HERE / 'focused-commands.json')
    assert all(row['exit'] == 0 for row in commands)
    whole = next(row['tests'] for row in commands if row['name'] == 'whole-library-tests')
    focused = next(row['tests'] for row in commands if row['name'] == 'focused-tests')
    portable = read(HERE / 'portable.json')
    assert portable['checks'] == portable['passed'] and not portable['errors']
    assert read(HERE / 'catalog-rebuild.json')['passed']
    prior = read(HERE / 'prior-evidence-readback.json')
    for checkpoint, record in prior.items():
        source = HERE.parent / checkpoint
        evidence = read(source / 'run.json')['evidence_sha256']
        assert len(evidence) == record['indexed_files']
        assert all(sha(source / p) == h for p, h in evidence.items())
    baseline = read(HERE / 'source-baseline.json')
    pre_edit = read(HERE / 'pre-edit-manifest.json')
    assert all(sha(HERE / 'pre-edit' / p) == h == baseline['files'][p]
               for p, h in pre_edit.items())
    forward = HERE / 'forward-review'
    assertions = read(forward / 'independent-assertion-outcomes.json')
    assert assertions['failed'] == 0 and assertions['passed'] == assertions['assertions']
    for p, h in read(forward / 'final-artifact-manifest.json').items():
        assert sha(forward / p) == h, p
    source_hashes = read(forward / 'package-hashes-after.json')
    assert source_hashes == read(forward / 'package-hashes-before.json')
    assert all(sha(ROOT / 'skills/investment-research' / p) == h for p, h in source_hashes.items())
    for p, h in read(HERE / 'forward-review-copy-readback.json')['file_sha256'].items():
        assert sha(forward / p) == h, p
    caps = read(ROOT / 'catalog/investment-research-capabilities.json')
    package_records = {}
    for row in caps['capabilities'] + caps['retained_legacy'] + caps['shared_owners']:
        if row.get('support_status') == 'planned':
            continue
        package = ROOT / row['path']
        manifest = package / 'references/package-manifest.json'
        inventory = read(manifest)['files']
        actual = {str(p.relative_to(package)): sha(p) for p in package.rglob('*')
                  if p.is_file() and p != manifest and '__pycache__' not in p.parts
                  and p.name != '.DS_Store' and p.suffix != '.pyc'}
        assert actual == inventory, row['name']
        package_records[row['name']] = {'manifest': str(manifest.relative_to(ROOT)),
                                       'sha256': sha(manifest), 'files': len(inventory)}
    counts = read(HERE / 'new-regression-counts.json')
    before, after = read(HERE / 'before-repair/report.json'), read(HERE / 'after-repair/report.json')
    assert before['passed'] and after['passed'] and before['cases'] == after['cases'] == 14
    assert [r['original_sha256'] for r in before['records']] == [r['original_sha256'] for r in after['records']]
    summary = f'''# Remaining findings repair validation

This checkpoint resolves the three findings from the follow-up review: live legacy
surveillance bypass, issuer-credit missingness, and capability-version drift.
[Implementation and migration](../remaining-findings-repairs-implementation.md)
records issuer credit 0.2.1, surveillance 0.4.1 and router 0.4.2.

| Check | Final result | Evidence |
|---|---|---|
| Full repository regressions | {whole:,} passed | [Log](whole-library-tests.log), [commands](whole-commands.json) |
| Focused Investment Research regressions | {focused:,} passed | [Log](focused-tests.log), [commands](focused-commands.json) |
| New regression methods | {sum(counts.values())} passed | [Method inventory](new-regression-counts.json) |
| Isolated portable package execution | {portable['passed']} checks across {portable['packages']} packages passed | [Report](portable.json) |
| Metadata, specification and references | 395 packages; zero errors or warnings | [Log](skills.log) |
| Structure and all 42 native/canonical/bundled versions | Passed | [Log](structure.log), [version changes](version-delta.json) |
| Shared resources, exact manifests and indexes | Passed | [Resources](resources.log), [indexes](index.log) |
| Isolated saved-catalog rebuild | JSON and CSV byte equal | [Proof](catalog-rebuild.json) |
| Public-command before/after replay | 14 identical inputs in each run | [Before](before-repair/report.json), [after](after-repair/report.json) |
| Independent fresh skill use | {assertions['passed']} assertions passed; seven outputs reconstructed | [Review](forward-review/review-summary.txt), [assertions](forward-review/independent-assertion-outcomes.json), [draft](forward-review/analyst-draft.txt) |
| Preservation | 1,926 earlier phase and repair files unchanged | [Audit](preservation.json), [baseline](source-baseline.json) |

Counts overlap. New tests are included in both suites; portable checks, request
cases and independent assertions are separate inventories, not additive totals.

## Findings and regression evidence

Legacy requests are rejected at all three live public entrypoints, including through
the historical Asset Management alias. Relabeling an old request/output cannot
bypass native validation or detached-original reconstruction. Tests cover future
reported periods, undated/stale/unmapped quotes, unknown schema labels, malformed
JSON, current complete/partial behavior, original binding and output mutation.
Frozen historical code and packets remain available as historical evidence.

Issuer tests separately cover omission and explicit null for all seven nullable
financial values, unavailable debt reconciliation/inclusion/principal, genuinely
zero and signed values, nonpositive denominators and independent retained measures.
Original hashes preserve the difference between omitted and null inputs; partial
status cannot be changed to complete, missing metrics cannot be invented as zero,
and original data is never filled in by calculation.

Version tests compare all 42 installed packages to both current registries, including
stale values copied into both registries, missing fields, malformed values and native
metadata drift. Catalog changes are restricted to three package versions and four
capability rows; historical phase inventory versions remain unchanged.

The [first full-suite run](integration-whole-library-tests.log) exposed four active
Asset Management test expectations that still assumed successful legacy execution.
Their original source is preserved. Historical maturity/source assertions retain
their financial expectations and now explicitly execute frozen prior source;
current alias tests separately enforce migration and the repaired contract. The
[initial focused run](integration-focused-tests.log) passed 527 tests before those
alias integration regressions were added. Final logs above supersede neither
historical checkpoint: they record the current repaired sources.

## Independent use and readback

The independent reviewer read published skills, schemas and input fixtures only for
structure, without prior conclusions or expected golden outputs. Raw synthetic facts
and rational expectations were saved before execution. Ten request/original pairs
include five issuer cases, four surveillance cases and a received legacy intake.
Seven computed outputs remain appropriately partial for unresolved priority or
maturity coverage; two annual/interim mismatches and the legacy request reject.

Independent arithmetic gives EBITDA96, debt360, cash24, interest12, OCF54, capex18,
FFO42 and a cited principal366 less6 carrying bridge. Supported gross/net/interest
ratios are 3.75x/3.5x/8x; free cash flow is36 and FFO/debt is7/60. Comparable supplied
quotes widen44.75bp. Missing evidence withholds dependent results while preserving
other supported measures. The review retains a minor generic diagnostic-wording
observation; no numerical or control failure was observed in this bounded exercise.

All64 reviewed package-file hashes match current source. The complete102-file
independent directory was copied and read back byte equal. The [copy proof](forward-review-copy-readback.json)
and run record bind the artifacts. The pre-edit manifest retains{len(pre_edit)}
original files with hashes equal to the20,387-file dirty-checkout baseline. Earlier
control/evidence-reconciliation checkpoint indexes (522 and444 files) were also
read back unchanged. [Source diff](changed-existing-sources.patch) compares current
edits with those originals rather than the aggregate Git diff.

## Limits

Repository gates pass. The installed auxiliary skill-creator validator still rejects
the repository's pre-existing supported `compatibility` field; [raw results](skill-creator-quick-validation.json)
are retained. Supported metadata was not removed to accommodate that allowlist.

The saved-catalog rebuild does not reconcile the external authoritative workbook.
These are supplied-data software controls, not source authentication, practitioner
or institutional acceptance. The broader blueprint's workflow acceptance, source
integration and deployment work remains separate. No external action was taken.
'''
    # Use normal prose spacing while retaining the independently recorded values.
    for a, b in [('EBITDA96','EBITDA 96'),('debt360','debt 360'),('cash24','cash 24'),
                 ('interest12','interest 12'),('OCF54','OCF 54'),('capex18','capex 18'),
                 ('FFO42','FFO 42'),('principal366','principal 366'),('less6','less 6'),
                 ('is36','is 36'),('is7/60','is 7/60'),('widen44.75bp','widen 44.75 bp'),
                 ('All64','All 64'),('complete102-file','complete 102-file'),
                 ('retains'+str(len(pre_edit)),'retains '+str(len(pre_edit))),
                 ('the20,387','the 20,387'),('and444','and 444')]:
        summary = summary.replace(a, b)
    (HERE / 'README.md').write_text(summary)
    # Create the final filenames before auditing so the saved inventory is stable.
    for name in ('preservation.json', 'run.json'):
        if not (HERE / name).exists():
            write(HERE / name, {})
    spec = importlib.util.spec_from_file_location('repair_preservation', ROOT / 'tools/check_ir_remaining_findings_preservation.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    preservation = module.audit(baseline)
    assert preservation['passed'], preservation['unexpected_changes']
    assert preservation['protected_evidence_files'] == 1926
    write(HERE / 'preservation.json', preservation)
    changed = {row['path'] for row in preservation['changes'] + preservation['new_files']
               if not row['path'].startswith(str(HERE.relative_to(ROOT)) + '/')}
    changed.update(record['manifest'] for record in package_records.values())
    sources = {path: sha(ROOT / path) for path in sorted(changed)}
    artifacts = {str(path.relative_to(HERE)): sha(path) for path in sorted(HERE.rglob('*'))
                 if path.is_file() and path != HERE / 'run.json'}
    record = {
        'schema_version': 'ir-remaining-findings-repair-run/1.0',
        'completed_at': datetime.now(timezone.utc).isoformat(),
        'python': sys.version, 'interpreter': sys.executable,
        'validation_pythonpath': '/private/tmp/ir-phase1-validation-venv/lib/python3.9/site-packages',
        'fixes': {'legacy_live_surveillance': 'migration-required',
                  'issuer_missing_evidence': 'partial-with-dependent-results-withheld',
                  'capability_versions': '42-native-canonical-bundled-parity'},
        'versions': {row['name']: row['package_version'] for row in caps['capabilities']
                     if row['name'] in ('issuer-credit-researcher', 'issuer-credit-surveillance-reviewer', 'investment-research-router')},
        'commands': commands, 'new_regression_methods': counts,
        'portable': {key: portable[key] for key in ('packages', 'checks', 'passed', 'errors')},
        'before_after_cases': 14, 'identical_originals': True,
        'independent_review': {'cases': 10, 'outputs_reconstructed': 7, 'assertions_passed': assertions['passed'],
                               'assertions_failed': 0, 'current_package_files_verified': len(source_hashes),
                               'copied_artifacts': read(HERE / 'forward-review-copy-readback.json')['files_copied']},
        'prior_indexed_evidence': prior, 'pre_edit_files': len(pre_edit),
        'baseline_sha256': sha(HERE / 'source-baseline.json'),
        'preservation': {key: preservation[key] for key in ('baseline_files', 'unchanged_baseline_files',
                         'protected_evidence_files', 'unexpected_changes', 'all_earlier_phase_and_repair_evidence_untouched', 'passed')},
        'packages': package_records, 'source_sha256': sources, 'evidence_sha256': artifacts,
        'evidence_hash_scope': 'All checkpoint files except this run record; paths relative to this directory',
        'repository_gates_passed': True, 'readback_verified': True,
        'auxiliary_quick_validation': 'pre-existing compatibility allowlist limitation',
        'professional_acceptance': 'not-established', 'external_action_taken': False,
    }
    write(HERE / 'run.json', record)
    assert read(HERE / 'run.json') == record
    assert all(sha(HERE / p) == h for p, h in record['evidence_sha256'].items())
    assert all(sha(ROOT / p) == h for p, h in record['source_sha256'].items())
    assert module.audit(baseline) == preservation
    print(json.dumps({'repository_tests': whole, 'focused_tests': focused,
                      'new_regression_methods': sum(counts.values()), 'portable_checks': portable['passed'],
                      'protected_evidence_files': 1926, 'evidence_hashes_verified': len(artifacts),
                      'source_hashes_verified': len(sources), 'passed': True}))


if __name__ == '__main__':
    main()
