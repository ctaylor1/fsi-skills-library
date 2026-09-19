"""Phase 2 offline workflow framing; domain methods own professional semantics.

Inputs and outputs retain supplied evidence. No source authentication or business
execution is performed. Native output validation recomputes from retained input.
"""
from __future__ import annotations

import copy
import json
from decimal import Decimal

from insurance_contract import amount, build_artifact, iso_date, stable_hash, validate_artifact

VERSION = 'insurance-foundation-1.0'
STATES = {'ready-for-review', 'needs-review', 'needs-data', 'not-applicable'}


def number(value):
    """Unknown stays None; malformed non-null or non-finite values fail."""
    if value is None:
        return None
    return amount(value)


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def validate_base(doc):
    if not isinstance(doc, dict):
        return ['input must be an object']
    errors = []
    try:
        stable_hash(doc)
    except ValueError as exc:
        errors.append(str(exc))
    if not _text(doc.get('case_id')):
        errors.append('case_id is required')
    try:
        iso_date(doc.get('as_of'))
    except (ValueError, TypeError):
        errors.append('as_of must be a calendar date YYYY-MM-DD')
    context = doc.get('context')
    if not isinstance(context, dict):
        errors.append('context must be an object')
    else:
        for key in ('capacity', 'represented_party', 'object_id', 'jurisdiction', 'line_of_business'):
            if not _text(context.get(key)):
                errors.append(f'context.{key} is required; use explicit unknown when unresolved')
    if not isinstance(doc.get('data'), dict):
        errors.append('data must contain the native workflow input object')
    sources = doc.get('sources')
    if not isinstance(sources, list):
        errors.append('sources must be a list (empty is allowed as an evidence gap)')
    else:
        seen = set()
        for i, row in enumerate(sources):
            if not isinstance(row, dict) or not _text(row.get('source_ref')) or not _text(row.get('version')):
                errors.append(f'sources[{i}] requires source_ref and version')
                continue
            if row['source_ref'] in seen:
                errors.append(f'duplicate source_ref: {row["source_ref"]}; disambiguate versions')
            seen.add(row['source_ref'])
            if row.get('as_of') is not None:
                try:
                    iso_date(row['as_of'])
                except (ValueError, TypeError):
                    errors.append(f'sources[{i}].as_of must be a calendar date')
    issues = doc.get('unresolved_issues')
    if not isinstance(issues, list) or any(not _text(x) for x in issues):
        errors.append('unresolved_issues must explicitly list open input questions')
    upstream = doc.get('upstream_artifacts', [])
    if not isinstance(upstream, list):
        errors.append('upstream_artifacts must be a list')
    else:
        for i, artifact in enumerate(upstream):
            errors.extend(f'upstream_artifacts[{i}]: {e}' for e in validate_artifact(artifact))
    return errors


def sources_for(doc, refs):
    """Return evidence-reference errors, not evidence or a trust verdict."""
    if isinstance(refs, str):
        refs = [refs]
    if not isinstance(refs, list) or not refs or any(not _text(x) for x in refs):
        return ['source_refs must identify supplied versioned evidence']
    available = {s['source_ref'] for s in doc.get('sources', []) if isinstance(s, dict) and _text(s.get('source_ref'))}
    return [f'unresolved source reference: {ref}' for ref in refs if ref not in available]


def profile_issues(doc, profile):
    """Check supplied rule profile scope; never infer applicable law from geography."""
    if not isinstance(profile, dict):
        return ['reviewed rule profile unavailable']
    issues = []
    for key in ('profile_id', 'version'):
        if not _text(profile.get(key)):
            issues.append(f'rule profile {key} missing')
    issues.extend(sources_for(doc, profile.get('source_refs')))
    for field, context_key in (('jurisdictions', 'jurisdiction'), ('lines_of_business', 'line_of_business')):
        values = profile.get(field)
        if not isinstance(values, list) or any(not _text(x) for x in values) or doc.get('context', {}).get(context_key) not in values:
            issues.append(f'rule profile {field} does not establish this request scope')
    try:
        start, end, day = iso_date(profile.get('effective_from')), iso_date(profile.get('effective_to')), iso_date(doc.get('as_of'))
        if start > end or not start <= day <= end:
            issues.append('rule profile is not effective at the requested as_of date')
    except (ValueError, TypeError):
        issues.append('rule profile requires valid effective_from and effective_to dates')
    return issues


def _jsonable(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def run(doc, producer, evaluator, validator=None):
    errors = validate_base(doc)
    if not errors and validator:
        errors.extend(validator(doc))
    if errors:
        raise ValueError('; '.join(errors))
    # Evaluators cannot mutate the evidence retained in the output.
    native = _jsonable(evaluator(copy.deepcopy(doc)))
    if not isinstance(native, dict) or native.get('status') not in STATES:
        raise ValueError('native evaluator must return a valid status')
    findings = native.get('findings')
    if not isinstance(findings, list) or not isinstance(native.get('results'), dict):
        raise ValueError('native evaluator requires findings list and results object')
    for item in findings:
        if not isinstance(item, dict) or not _text(item.get('code')) or not _text(item.get('message')) or item.get('severity') not in {'gap', 'review', 'info'}:
            raise ValueError('finding requires code, message and gap/review/info severity')
        if not isinstance(item.get('source_refs'), list) or any(not _text(x) for x in item['source_refs']):
            raise ValueError('finding.source_refs must be a list')
    base_gaps = []
    context = doc['context']
    for key, value in context.items():
        if isinstance(value, str) and value.strip().lower() in {'unknown', 'n/a', 'na'}:
            base_gaps.append(f'context.{key} unresolved')
    if not doc['sources']:
        base_gaps.append('versioned source evidence unavailable')
    for source in doc['sources']:
        if source.get('as_of') and source['as_of'] > doc['as_of']:
            base_gaps.append(f'source {source["source_ref"]} postdates the requested as_of date')
    # A valid envelope is not evidence that it belongs to this customer/object.
    # Legitimate changes of capacity or identity require a source-bound mapping.
    mappings = doc.get('context_mappings', [])
    if not isinstance(mappings, list):
        mappings = []
        base_gaps.append('context_mappings must be a list of reviewed scope mappings')
    scope_fields = ('capacity', 'represented_party', 'object_id', 'jurisdiction', 'line_of_business')
    for upstream in doc.get('upstream_artifacts', []):
        changed = [key for key in scope_fields if upstream['context'].get(key) != context.get(key)]
        if changed:
            matches = [m for m in mappings if isinstance(m, dict)
                       and m.get('source_artifact_hash') == stable_hash(upstream)
                       and m.get('source_context') == upstream['context']
                       and m.get('target_context') == context
                       and _text(m.get('reviewed_by')) and _text(m.get('basis'))
                       and not sources_for(doc, m.get('source_refs'))]
            if len(matches) != 1:
                base_gaps.append('upstream context differs (' + ', '.join(changed) + '); one source-bound reviewed context mapping required')
        if upstream.get('as_of') and upstream['as_of'] > doc['as_of']:
            base_gaps.append('upstream artifact postdates the requested as_of date')
    for item in findings:
        if item['source_refs']:
            base_gaps.extend(sources_for(doc, item['source_refs']))
    for gap in dict.fromkeys(base_gaps):
        findings.append({'code': 'foundation-evidence-gap', 'message': gap, 'severity': 'gap', 'source_refs': []})
    issues = list(dict.fromkeys(doc['unresolved_issues'] + [f['message'] for f in findings if f['severity'] in {'gap', 'review'}]))
    out = {'schema_version': VERSION, 'producer': producer, 'case_id': doc['case_id'],
           'as_of': doc['as_of'], 'context': copy.deepcopy(context),
           'status': native['status'], 'findings': findings, 'results': native['results'],
           'completeness': native.get('completeness', 'partial'),
           'evaluability': native.get('evaluability', 'partial'), 'unresolved_issues': issues,
           'action_taken': False, 'human_review_required': True,
           'approval': 'not_requested', 'execution': 'not_performed',
           'source_document': copy.deepcopy(doc)}
    if any(f['severity'] == 'gap' for f in findings) or doc['unresolved_issues']:
        out['status'] = 'needs-data'
        if out['completeness'] == 'complete':
            out['completeness'] = 'partial'
        if out['evaluability'] == 'evaluable':
            out['evaluability'] = 'partial'
    elif any(f['severity'] == 'review' for f in findings) and out['status'] == 'ready-for-review':
        out['status'] = 'needs-review'
    # Mirror the established contract's inherited status floor at top level.
    envelope = build_artifact(doc, out, producer=producer, artifact_type='insurance-workflow-review',
                              completeness=out['completeness'], evaluability=out['evaluability'], issues=issues)
    out['completeness'], out['evaluability'] = envelope['completeness'], envelope['evaluability']
    out['unresolved_issues'] = envelope['unresolved_issues']
    if (out['completeness'] != 'complete' or out['evaluability'] != 'evaluable') and out['status'] == 'ready-for-review':
        out['status'] = 'needs-data'
    out['artifact'] = build_artifact(doc, out, producer=producer, artifact_type='insurance-workflow-review',
                                    completeness=out['completeness'], evaluability=out['evaluability'], issues=out['unresolved_issues'])
    return out


def check_output(output, producer, evaluator, validator=None):
    if not isinstance(output, dict) or not isinstance(output.get('source_document'), dict):
        return ['output must retain source_document']
    try:
        expected = run(output['source_document'], producer, evaluator, validator)
        errors = validate_artifact(output.get('artifact'), input_doc=output['source_document'], output=output)
        if output != expected:
            errors.append('output differs from native recomputation of retained evidence')
        return errors
    except (ValueError, TypeError, KeyError, AttributeError, ArithmeticError) as exc:
        return [f'cannot reproduce output: {exc}']


def main(mode, producer, evaluator, validator=None, argv=None):
    """Small shared CLI; package wrappers supply their native validator/evaluator."""
    import sys
    from pathlib import Path
    args = sys.argv[1:] if argv is None else argv
    try:
        doc = json.loads(Path(args[0]).read_text()) if args else json.load(sys.stdin)
        if mode == 'calculate':
            print(json.dumps(run(doc, producer, evaluator, validator), indent=2, allow_nan=False))
            return 0
        errors = check_output(doc, producer, evaluator, validator) if mode == 'output' else validate_base(doc)
        if mode == 'input' and not errors and validator:
            errors += validator(doc)
        print(json.dumps({'errors': errors, 'valid': not errors}, indent=2))
        return int(bool(errors))
    except (ValueError, TypeError, KeyError, OSError, ArithmeticError) as exc:
        print(json.dumps({'errors': [str(exc)], 'valid': False}))
        return 1
