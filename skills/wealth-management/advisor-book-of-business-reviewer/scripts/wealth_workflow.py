"""Shared P2 evidence, Decimal, reconstruction and CLI primitives. No external actions.

Canonical source; bundled copies must remain byte-identical via sync_wealth_contract.py.
"""
import json
import sys
from copy import deepcopy
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

from wealth_contract import iso_date, nonempty, source_errors, validate_envelope, validate_output_envelope


def number(value, low=0, high=10**15):
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        return False
    try:
        parsed = Decimal(str(value))
        return parsed.is_finite() and parsed.as_tuple().exponent >= -8 and Decimal(str(low)) <= parsed <= Decimal(str(high))
    except (InvalidOperation, ValueError):
        return False


def dec(value):
    return Decimal(str(value))


def money(value):
    return str(dec(value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))


def enum(value, options):
    return isinstance(value, str) and value in options


def texts(value, allow_empty=False):
    return isinstance(value, list) and (allow_empty or bool(value)) and all(nonempty(x) for x in value) and len(value) == len(set(value))


def rows(doc, key, errors, identifier=None):
    value = doc.get(key)
    if not isinstance(value, list) or len(value) > 1000 or any(not isinstance(x, dict) for x in value):
        errors.append(f'{key} must be an explicit list of at most 1000 objects')
        return []
    if identifier:
        seen = set()
        for row in value:
            rid = row.get(identifier)
            if not nonempty(rid) or (isinstance(rid, str) and rid in seen):
                errors.append(f'{key}.{identifier} must be nonempty and unique')
            if isinstance(rid, str):
                seen.add(rid)
    return value


def base_errors(doc):
    errors = validate_envelope(doc)
    if errors:
        return errors
    if 'unresolved_issues' in doc:
        errors.append('map unresolved_issues into required upstream_issues records; do not supply both schemas')
    policy = doc.get('policy')
    if not isinstance(policy, dict):
        errors.append('policy must be an object')
    else:
        for key in ('version', 'owner'):
            if not nonempty(policy.get(key)):
                errors.append(f'policy.{key} is required')
        if policy.get('capacity') != doc['engagement']['capacity'] or policy.get('jurisdiction') != doc['engagement']['jurisdiction']:
            errors.append('policy applicability must match engagement capacity and jurisdiction')
        effective, until = iso_date(policy.get('effective_date')), iso_date(policy.get('valid_until'))
        if effective is None or until is None or not effective <= iso_date(doc['as_of']) <= until:
            errors.append('policy requires current effective_date and valid_until')
    for issue in rows(doc, 'upstream_issues', errors):
        if any(not nonempty(issue.get(k)) for k in ('artifact_id', 'code', 'message')) or not enum(issue.get('status'), {'unresolved', 'resolved'}):
            errors.append('upstream issue requires artifact_id, code, message and explicit unresolved/resolved status')
        if issue.get('status') == 'resolved':
            resolution = issue.get('resolution')
            if not isinstance(resolution, dict) or any(not nonempty(resolution.get(k)) for k in ('owner', 'reference')):
                errors.append('resolved issue requires attributed resolution owner/reference')
            elif iso_date(resolution.get('as_of')) is None or resolution['as_of'] > doc['as_of']:
                errors.append('resolution requires a nonfuture as_of date')
    return errors


def add(findings, code, message, path, **context):
    findings.append(dict(code=code, message=message, path=path, **context))


def cited(row, doc, findings, path):
    errors = source_errors(row.get('source_ids'), doc)
    for error in errors:
        add(findings, 'evidence-gap', error, path)
    return not errors


def base_findings(doc):
    findings = []
    cited(doc['policy'], doc, findings, 'policy')
    cited(doc['engagement'], doc, findings, 'engagement')
    for index, issue in enumerate(doc['upstream_issues']):
        path = f'upstream_issues[{index}]'
        cited(issue, doc, findings, path)
        if issue['status'] == 'unresolved':
            add(findings, 'upstream-unresolved', issue['message'], path,
                upstream_artifact_id=issue['artifact_id'], upstream_code=issue['code'], source_ids=deepcopy(issue.get('source_ids')))
        else:
            cited(issue['resolution'], doc, findings, path + '.resolution')
    return findings


def common_result(doc):
    return {'input_snapshot': deepcopy(doc), 'policy': deepcopy(doc['policy']), 'upstream_issues': deepcopy(doc['upstream_issues']),
            'scope': 'Supplied evidence only; human review required; no approval or execution.',
            'handoff_context': {k: deepcopy(doc[k]) for k in ('household_id', 'request_id', 'as_of', 'engagement', 'sources', 'upstream_issues')}}


def validate_result(out, skill, build):
    errors = validate_output_envelope(out, skill)
    if errors:
        return errors
    try:
        expected = build(out['result'].get('input_snapshot'))
        if out != expected:
            errors.append('output differs from full reconstruction of source snapshot, calculations, findings or identity')
    except (ValueError, TypeError, KeyError, ArithmeticError) as exc:
        errors.append(f'invalid input snapshot: {exc}')
    return errors


def run_cli(mode, validate, build, validate_output, script_path, fixture='request.json'):
    args = sys.argv[1:]
    if len(args) != 1:
        print('usage: python scripts/' + Path(script_path).name + ' INPUT.json | --selftest')
        return 2
    try:
        path = Path(script_path).resolve().parents[1] / 'evals/files' / fixture if args == ['--selftest'] else Path(args[0])
        doc = json.loads(path.read_text())
        if mode == 'compute':
            print(json.dumps(build(doc), indent=2, allow_nan=False))
            return 0
        if mode == 'output' and args == ['--selftest']:
            doc = build(doc)
        errors = validate(doc) if mode == 'input' else validate_output(doc)
        print(json.dumps({'errors': errors}))
        return int(bool(errors))
    except (OSError, ValueError, TypeError, KeyError, ArithmeticError) as exc:
        print(json.dumps({'errors': [str(exc)]}))
        return 1
