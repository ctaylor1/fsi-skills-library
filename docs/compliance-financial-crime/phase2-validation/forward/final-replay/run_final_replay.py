"""Retain original expectations and replay unchanged synthetic supplied inputs.

This runner writes only under final-replay. Native validators receive separately
retained inputs; no source truth, legal approval, or institutional acceptance is
inferred from deterministic reconstruction.
"""
from __future__ import annotations

import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path('/Users/taylor/DevRepo/Skills/fsi-skills-library')
ORIGINAL = ROOT / 'docs/compliance-financial-crime/phase2-validation/forward'
DEST = ORIGINAL / 'final-replay'
PACKAGES = ROOT / 'skills/compliance-financial-crime'
PYTHON = Path('/tmp/cfc-phase2-venv/bin/python')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def inventory(paths):
    return {str(p.relative_to(ROOT)): sha(p) for p in sorted(set(paths))}


def summary(checks):
    return {'passed': sum(c['passed'] for c in checks), 'total': len(checks),
            'failed': sum(not c['passed'] for c in checks), 'checks': checks}


def substantive_amendment():
    """Add explicitly reviewed event/additivity assertions to the retained substantive intake."""
    original_path = ORIGINAL / 'edd-substantive/input.initial.json'
    template_path = ORIGINAL / 'edd-duplicated-economic-event/input.amended-event-identity.json'
    original = json.loads(original_path.read_text())
    template = json.loads(template_path.read_text())
    amended = copy.deepcopy(original)
    source_ref = 'economic-event-review-workpaper-substantive'
    source = {'source_ref': source_ref, 'version': 'synthetic-final-replay-v1',
        'received_at': '2026-10-03', 'publication_date': '2026-10-03',
        'classification': 'customer_pii', 'permitted_audiences': ['internal_review'], 'facts': []}
    provenance = []
    counter = 0

    def assertion(value, justification, grounded_fact_ids):
        nonlocal counter
        counter += 1
        fact_id = 'FWD-EDD-SUBSTANTIVE-economic-review-' + str(counter)
        source['facts'].append({'fact_id': fact_id, 'value': copy.deepcopy(value), 'excerpt': justification})
        provenance.append({'fact_id': fact_id, 'value': value, 'justification': justification,
            'original_fact_ids': grounded_fact_ids, 'status': 'explicit-synthetic-supplied-review-assertion-unverified'})
        return {'value': copy.deepcopy(value), 'source_refs': [source_ref], 'fact_ids': [fact_id]}

    templates = {c['claim_id']: c for c in template['data']['wealth_funds_claims']}
    for claim in amended['data']['wealth_funds_claims']:
        identities = {e['evidence_id']: e['economic_event']['value'] for e in templates[claim['claim_id']]['corroboration']}
        for evidence in claim['corroboration']:
            identity = copy.deepcopy(identities[evidence['evidence_id']])
            assert identity['amount'] == evidence['amount']['value']
            assert identity['date'] == evidence['date']['value'] and identity['currency'] == evidence['currency']
            ids = [fid for field in ['amount', 'date', 'currency_evidence', 'description'] for fid in evidence[field]['fact_ids']]
            justification = ('Synthetic independent identity review: ' + evidence['description']['value']
                + '. The retained original exact amount/date/currency/description facts ' + ','.join(ids)
                + ' identify this scoped receipt or pre-existing wealth component. Event identity is a supplied review assertion, not authentication.')
            evidence['economic_event'] = assertion(identity, justification, ids)
        additive = copy.deepcopy(templates[claim['claim_id']]['additivity']['value'])
        ids = [fid for e in claim['corroboration'] for field in ['amount', 'date', 'currency_evidence', 'description'] for fid in e[field]['fact_ids']]
        justification = ('Synthetic independent additivity review: original descriptions identify an actual first USD300000 credit and a distinct final USD75000 credit on separate dates.'
            if claim['kind'] == 'source_of_funds' else
            'Synthetic independent additivity review: the single documented pre-existing USD900000 wealth balance explicitly excludes sale proceeds; no additional wealth components are introduced.')
        claim['additivity'] = assertion(additive, justification + ' Original facts: ' + ','.join(ids) + '. Human review remains required.', ids)
    amended['sources'].append(source)
    amended['workflow']['sources'].append({'source_ref': source_ref, 'version': source['version']})
    stripped = copy.deepcopy(amended)
    stripped['sources'].pop()
    stripped['workflow']['sources'].pop()
    for claim in stripped['data']['wealth_funds_claims']:
        claim.pop('additivity')
        for evidence in claim['corroboration']:
            evidence.pop('economic_event')
    assert stripped == original
    folder = DEST / 'edd-substantive-amended'
    folder.mkdir(exist_ok=True)
    path = folder / 'input.amended-event-identity.json'
    dump(path, amended)
    dump(folder / 'amendment-provenance.json', {'original_input': str(original_path.relative_to(ROOT)),
        'original_input_sha256': sha(original_path), 'template_input': str(template_path.relative_to(ROOT)),
        'amended_input_sha256': sha(path), 'only_new_event_additivity_claims_added': stripped == original,
        'original_corroboration_rows_preserved': True, 'additional_duplicate_document': False,
        'added_facts': provenance, 'source_authentication': 'not-established'})
    return path


def main():
    if (DEST / 'replay-runs.json').exists():
        raise SystemExit('Completed replay exists; preserve evidence and use another destination')
    DEST.mkdir(exist_ok=True)
    original_runs = json.loads((ORIGINAL / 'initial-runs.json').read_text())
    original_assessment = json.loads((ORIGINAL / 'forward-assessment.json').read_text())
    for retained in original_runs:
        assert sha(ORIGINAL / retained['case'] / 'input.initial.json') == retained['input_sha256']
        if 'output_sha256' in retained:
            assert sha(ORIGINAL / retained['case'] / 'output.initial.json') == retained['output_sha256']
    skills = sorted({r['skill'] for r in original_runs})
    method_paths = []
    for skill in skills:
        method_paths += [p for p in (PACKAGES / skill).rglob('*')
                         if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'
                         and p.name != 'package-manifest.json']
    immutable_paths = [ORIGINAL / n for n in ['assessment.md', 'scenario-expectations.md',
        'forward-assessment.json', 'initial-runs.json', 'runner.sha256.txt',
        'cdd-to-edd-reviewed-mapping.json']]
    for run in original_runs:
        case = ORIGINAL / run['case']
        immutable_paths += [case / 'input.initial.json', case / 'run.json']
        for cmd in run['commands']:
            immutable_paths += [case / (cmd['stage'] + ext) for ext in ['.stdout.txt', '.stderr.txt']]
        for name in ['output.initial.json', 'output.tampered.json']:
            if (case / name).exists():
                immutable_paths.append(case / name)
    before_methods = inventory(method_paths)
    before_originals = inventory(immutable_paths)
    dump(DEST / 'method-hashes.before.json', before_methods)
    dump(DEST / 'original-artifact-hashes.before.json', before_originals)
    for filename in ['scenario-expectations.md', 'forward-assessment.json', 'initial-runs.json',
                     'cdd-to-edd-reviewed-mapping.json']:
        shutil.copyfile(ORIGINAL / filename, DEST / ('original-' + filename))
    shutil.copyfile('/tmp/cfc_forward_assess.py', DEST / 'original-assessor.py')
    dump(DEST / 'frozen-pre-run-expectations.json', {
        'original_assertions': original_assessment['domain_assertions']['checks'],
        'original_cli_expectations': original_assessment['cli_checks']['checks'],
        'retention': 'All original numeric expectations remain unchanged; withheld totals are not counted as numerical passes.',
        'current_intake_rejections': ['cdd-duplicate-receipt', 'mule-duplicate-identity'],
        'intake_rejection_basis': 'Original pre-run CDD narrative explicitly permits rejection for the duplicate receipt; mule duplicate requires rejection.',
        'amended_inputs': 'Separate event identity/additivity amendments for substantive and duplicate-document EDD; neither substitutes for original inputs.',
        'amended_quantitative_expectations': {
            'sale_corroborated_amount': '375000.00', 'sale_difference': '0.00',
            'wealth_difference': '300000.00', 'sale_unique_event_count': 2,
            'sale_duplicate_document_count': 1},
        'frozen_before': datetime.now(timezone.utc).isoformat()})
    runs, outputs, cli = [], {}, []
    schema_checks = []

    def run(case_name, skill, source_input, reject=False, amended=False):
        folder = DEST / case_name
        folder.mkdir(exist_ok=True)
        input_path = folder / 'input.retained.json'
        shutil.copyfile(source_input, input_path)
        if amended and case_name == 'edd-duplicated-economic-event-amended':
            amended_input = json.loads(input_path.read_text())
            duplicate_original_path = ORIGINAL / 'edd-duplicated-economic-event/input.initial.json'
            duplicate_original = json.loads(duplicate_original_path.read_text())
            original_sources = {s['source_ref'] for s in duplicate_original['sources']}
            supplements = [s for s in amended_input['sources'] if s['source_ref'] not in original_sources]
            stripped = copy.deepcopy(amended_input)
            stripped['sources'] = [s for s in stripped['sources'] if s['source_ref'] in original_sources]
            stripped['workflow']['sources'] = [s for s in stripped['workflow']['sources'] if s['source_ref'] in original_sources]
            for claim in stripped['data']['wealth_funds_claims']:
                claim.pop('additivity')
                for evidence in claim['corroboration']:
                    evidence.pop('economic_event')
            assert stripped == duplicate_original
            dump(folder / 'amendment-provenance.json', {
                'original_input': str(duplicate_original_path.relative_to(ROOT)),
                'original_input_sha256': sha(duplicate_original_path), 'amended_input_sha256': sha(input_path),
                'only_new_event_additivity_claims_added': True,
                'all_original_corroboration_rows_and_facts_preserved': True,
                'added_source_records_with_all_facts_and_justifications': supplements,
                'source_authentication': 'not-established'})
        entry = {'case': case_name, 'skill': skill, 'amended': amended,
                 'source_input': str(source_input.relative_to(ROOT)),
                 'input_sha256': sha(input_path), 'commands': [], 'expected_current_intake_rejection': reject}
        script_dir = PACKAGES / skill / 'scripts'

        def call(stage, argv, expected):
            completed = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True)
            stdout_path, stderr_path = folder / (stage + '.stdout.txt'), folder / (stage + '.stderr.txt')
            stdout_path.write_text(completed.stdout)
            stderr_path.write_text(completed.stderr)
            command = {'stage': stage, 'argv': argv, 'cwd': str(ROOT), 'exit_code': completed.returncode,
                'expected_current_exit_code': expected, 'passed': completed.returncode == expected,
                'stdout_sha256': sha(stdout_path), 'stderr_sha256': sha(stderr_path)}
            entry['commands'].append(command)
            cli.append({'case': case_name, **command})
            return completed

        prefix = [str(PYTHON), '-B']
        call('validate_input', prefix + [str(script_dir / 'validate_input.py'), str(input_path)], int(reject))
        calculated = call('calculate', prefix + [str(script_dir / 'calculate_or_transform.py'), str(input_path)], int(reject))
        if calculated.returncode == 0:
            output_path = folder / 'output.replayed.json'
            output_path.write_text(calculated.stdout)
            output = json.loads(calculated.stdout)
            outputs[case_name] = output
            entry['output_sha256'] = sha(output_path)
            call('validate_output', prefix + [str(script_dir / 'validate_output.py'), str(output_path),
                '--input', str(input_path)], 0)
            tampered = copy.deepcopy(output)
            tampered['action_taken'] = True
            tampered_path = folder / 'output.tampered.json'
            dump(tampered_path, tampered)
            entry['tampered_output_sha256'] = sha(tampered_path)
            call('reject_tampered_output', prefix + [str(script_dir / 'validate_output.py'), str(tampered_path),
                '--input', str(input_path)], 1)
            schema_path = PACKAGES / skill / 'references/output-schema.json'
            if schema_path.exists():
                import jsonschema
                schema = json.loads(schema_path.read_text())
                validator_type = jsonschema.validators.validator_for(schema)
                validator_type.check_schema(schema)
                errors = sorted(validator_type(schema, format_checker=jsonschema.FormatChecker()).iter_errors(output),
                                key=lambda e: str(e.path))
                schema_check = {'case': case_name, 'schema': str(schema_path.relative_to(ROOT)),
                    'schema_sha256': sha(schema_path), 'passed': not errors,
                    'errors': [{'path': list(e.path), 'message': e.message} for e in errors]}
                schema_checks.append(schema_check)
                dump(folder / 'published-output-schema-validation.json', schema_check)
        dump(folder / 'run.json', entry)
        runs.append(entry)
        print(json.dumps({'case': case_name, 'stages': {c['stage']: c['exit_code'] for c in entry['commands']}}), flush=True)

    for original in original_runs:
        run(original['case'], original['skill'], ORIGINAL / original['case'] / 'input.initial.json',
            reject=original['case'] in ['cdd-duplicate-receipt', 'mule-duplicate-identity'])
    amended_case = 'edd-duplicated-economic-event-amended'
    run(amended_case, 'enhanced-due-diligence-assessor',
        ORIGINAL / 'edd-duplicated-economic-event/input.amended-event-identity.json', amended=True)
    substantive_case = 'edd-substantive-amended'
    run(substantive_case, 'enhanced-due-diligence-assessor', substantive_amendment(), amended=True)
    dump(DEST / 'replay-runs.json', runs)

    # Replay the original assertion extraction logic and preserve every expected value.
    # The absent CDD result yields a literal unknown numeric value rather than a fake total.
    source = (DEST / 'original-assessor.py').read_text()
    extract = source[source.index('CHECKS=[]'):source.index('cli=[]')]
    extract = extract.replace("def r(case):return O[case]['results']",
        "def r(case):return O.get(case, {'results': {'observed_activity_total': None}})['results']")
    namespace = {'O': {k: v for k, v in outputs.items() if k not in [amended_case, substantive_case]}}
    exec(compile(extract, str(DEST / 'original-assessor.py'), 'exec'), namespace)
    checks = namespace['CHECKS']
    frozen = original_assessment['domain_assertions']['checks']
    assert [(c['case'], c['assertion'], c['expected']) for c in checks] == [
        (c['case'], c['assertion'], c['expected']) for c in frozen]
    withheld = {
        ('cdd-duplicate-receipt', 'Repeated receipt must not increase assessed unique activity'):
            'Current input validator and calculator reject duplicate monetary provenance; no total is produced. Pre-run narrative allowed rejection.',
        ('edd-substantive', 'Actual two sale credits reconcile exactly'):
            'Untyped original corroboration lacks explicit economic-event identity and additivity; total and difference withheld.',
        ('edd-substantive', 'Wealth gap retained'):
            'Untyped original wealth corroboration lacks disjoint-component additivity and event identity; difference withheld.',
        ('edd-duplicated-economic-event', 'Two documents about same tranche do not create additional proceeds'):
            'Original duplicate-document case lacks explicit event identity/additivity; total withheld. Amendment is tested separately.'}
    for check in checks:
        check['outcome'] = 'passed' if check['passed'] else 'withheld-under-current-evidence-contract' if (check['case'], check['assertion']) in withheld else 'failed'
        if not check['passed'] and (check['case'], check['assertion']) in withheld:
            check['explanation'] = withheld[check['case'], check['assertion']]

    legacy_cli = []
    actual_commands = {(c['case'], c['stage']): c for c in cli if c['case'] not in [amended_case, substantive_case]}
    for old in original_assessment['cli_checks']['checks']:
        actual = actual_commands.get((old['case'], old['stage']))
        legacy_cli.append({'case': old['case'], 'stage': old['stage'],
            'original_expected_exit_code': old['expected_exit_code'],
            'actual_exit_code': actual['exit_code'] if actual else None,
            'outcome': 'passed' if actual and actual['exit_code'] == old['expected_exit_code'] else
                       'changed-intake-rejection' if actual and old['case'] == 'cdd-duplicate-receipt' else 'not-executed-after-intake-rejection',
            'passed': bool(actual and actual['exit_code'] == old['expected_exit_code'])})
    safety = []

    def check_safety(case, name, actual, expected):
        safety.append({'case': case, 'assertion': name, 'actual': actual, 'expected': expected, 'passed': actual == expected})

    cdd_run = next(r for r in runs if r['case'] == 'cdd-duplicate-receipt')
    check_safety('cdd-duplicate-receipt', 'Duplicate provenance stops intake and computation',
        [c['exit_code'] for c in cdd_run['commands']], [1, 1])
    for case in ['edd-substantive', 'edd-duplicated-economic-event']:
        a = outputs[case]['results']['wealth_funds_assessments']
        check_safety(case, 'Missing event identity/additivity withholds both claim totals and differences',
            [[x['corroborated_amount'], x['difference'], x['economic_event_aggregation']['status']] for x in a],
            [[None, None, 'unknown-total-withheld'], [None, None, 'unknown-total-withheld']])
    a = outputs[amended_case]['results']['wealth_funds_assessments']
    check_safety(amended_case, 'Exact distinct sale total and difference', [a[0]['corroborated_amount'], a[0]['difference']], ['375000.00', '0.00'])
    check_safety(amended_case, 'Wealth gap computed under explicit disjoint-component evidence', a[1]['difference'], '300000.00')
    check_safety(amended_case, 'Distinct sale events counted once', a[0]['economic_event_aggregation']['unique_event_count'], 2)
    check_safety(amended_case, 'Duplicate document excluded from additional funds',
        sum(x['counting_status'] == 'duplicate-document-not-additional-funds' for x in a[0]['corroboration']), 1)
    check_safety(amended_case, 'Capacity excess and Unknown residual risk retained',
        [a[1]['capacity_review'], outputs[amended_case]['results']['residual_risk']['band']],
        ['exceeds-supplied-economic-capacity', 'Unknown'])
    amended_namespace = {'O': {**namespace['O'], 'edd-substantive': outputs[substantive_case],
        'edd-duplicated-economic-event': outputs[amended_case]}}
    exec(compile(extract, str(DEST / 'original-assessor.py'), 'exec'), amended_namespace)
    amended_assertions = []
    for check in amended_namespace['CHECKS']:
        if check['case'] in ['edd-substantive', 'edd-duplicated-economic-event']:
            check['case'] += '-amended'
            amended_assertions.append(check)
    a = outputs[substantive_case]['results']['wealth_funds_assessments']
    check_safety(substantive_case, 'Original two distinct credit records preserved and counted once',
        [a[0]['economic_event_aggregation']['unique_event_count'],
            sum(x['counting_status'] == 'counted-once' for x in a[0]['corroboration']),
            sum(x['counting_status'] == 'duplicate-document-not-additional-funds' for x in a[0]['corroboration'])], [2, 2, 0])

    after_methods, after_originals = inventory(method_paths), inventory(immutable_paths)
    dump(DEST / 'method-hashes.after.json', after_methods)
    dump(DEST / 'original-artifact-hashes.after.json', after_originals)
    stability = {'method_file_count': len(before_methods), 'original_artifact_count': len(before_originals),
        'method_inventory_scope': 'Six complete package trees excluding generated bytecode and package-manifest.json; includes runtime scripts, input/output schemas, instructions, reference contracts, and evaluation fixtures.',
        'methods_unchanged': before_methods == after_methods, 'original_artifacts_unchanged': before_originals == after_originals,
        'changed_methods': [p for p in before_methods if before_methods[p] != after_methods[p]],
        'changed_originals': [p for p in before_originals if before_originals[p] != after_originals[p]],
        'runner_sha256': sha(Path(__file__)), 'original_assessor_sha256': sha(DEST / 'original-assessor.py')}
    dump(DEST / 'stability.json', stability)
    report = {'original_scenarios': len(original_runs), 'original_native_outputs': len(outputs) - 2,
        'amended_scenarios': 2, 'amended_native_outputs': 2,
        'original_assertions': {'passed': sum(c['passed'] for c in checks),
            'withheld': sum(c['outcome'] == 'withheld-under-current-evidence-contract' for c in checks),
            'failed': sum(c['outcome'] == 'failed' for c in checks), 'total': len(checks), 'checks': checks},
        'original_cli_expectation_comparison': {**summary(legacy_cli),
            'outcome_counts': {name: sum(c['outcome'] == name for c in legacy_cli) for name in
                ['passed', 'changed-intake-rejection', 'not-executed-after-intake-rejection']}},
        'current_cli_checks': summary(cli), 'published_output_schema_checks': summary(schema_checks),
        'current_evidence_contract_checks': summary(safety), 'amended_edd_original_assertion_checks': summary(amended_assertions),
        'stability': stability,
        'scope': 'Supplied synthetic evidence; independent original-input reconstruction; no actual institutional/legal/authentication acceptance.',
        'professional_acceptance': 'not-established', 'source_authentication': 'not-established', 'legal_approval': 'not-established',
        'completed_at': datetime.now(timezone.utc).isoformat()}
    dump(DEST / 'final-replay-assessment.json', report)
    assert stability['methods_unchanged'] and stability['original_artifacts_unchanged']
    assert all(c['passed'] for c in cli + schema_checks + safety + amended_assertions)
    assert not any(c['outcome'] == 'failed' for c in checks)
    print(json.dumps({k: v for k, v in report.items() if k not in [
        'original_assertions', 'original_cli_expectation_comparison', 'current_cli_checks',
        'published_output_schema_checks', 'current_evidence_contract_checks', 'amended_edd_original_assertion_checks']}, indent=2))
    print(json.dumps({'original_assertions': {k: v for k, v in report['original_assertions'].items() if k != 'checks'},
        'current_cli_checks': {k: v for k, v in report['current_cli_checks'].items() if k != 'checks'},
        'published_output_schema_checks': {k: v for k, v in report['published_output_schema_checks'].items() if k != 'checks'},
        'current_evidence_contract_checks': {k: v for k, v in report['current_evidence_contract_checks'].items() if k != 'checks'}}))


if __name__ == '__main__':
    main()
