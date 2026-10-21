"""Portable Phase 2 supplied-evidence contract (MIT); no source/authority authentication."""
from __future__ import annotations

import argparse
import copy
from datetime import date
from decimal import Decimal, InvalidOperation
import json
import math
from pathlib import Path
import re
import sys

from native_integrity import attach_source, canonical_hash, validate_reconstruction

VERSION = 'compliance-foundation/2.0'
ROLES = {'control_operator', 'oversight', 'decision_support', 'operational_qa',
         'independent_testing', 'regulatory_affairs', 'privacy_review'}
CLASSIFICATIONS = {'compliance_confidential', 'customer_pii', 'mnpi', 'sar_restricted', 'legal_restricted'}
CONTEXT_KEYS = ('institution_id', 'legal_entity_id', 'capacity', 'represented_party',
                'object_id', 'object_type', 'jurisdiction', 'line_of_business', 'purpose')


def text(value):
    return isinstance(value, str) and bool(value.strip())


def known(value):
    return value is not None and (not isinstance(value, str) or
        value.strip().lower() not in {'', 'unknown', 'n/a', 'not-assessed', 'not_assessed', 'unavailable'})


def number(value, low=0, high=None):
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(value) and (low is None or value >= low) and (high is None or value <= high)
    except (OverflowError, TypeError):
        return False


def decimal(value):
    if isinstance(value, bool) or not isinstance(value, (int, float, str, Decimal)):
        raise ValueError('finite numeric value required')
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError('finite numeric value required') from exc
    if not result.is_finite():
        raise ValueError('finite numeric value required')
    return result


def day(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def records(value):
    return isinstance(value, list) and all(isinstance(row, dict) for row in value)


def strings(value, nonempty=False):
    return isinstance(value, list) and (bool(value) or not nonempty) and all(text(v) for v in value)


def unique_ids(rows, key):
    return records(rows) and all(text(row.get(key)) for row in rows) and len({row[key] for row in rows}) == len(rows)


def _classification_allows(source, target):
    if not isinstance(source, str) or not isinstance(target, str):
        return False
    if source == 'compliance_confidential':
        return target in CLASSIFICATIONS
    if source == 'customer_pii':
        return target in CLASSIFICATIONS - {'compliance_confidential'}
    return source == target


def validate_common(doc, object_types=None):
    errors = []
    if not isinstance(doc, dict):
        return ['input must be an object']
    try:
        canonical_hash(doc)
    except (ValueError, TypeError, OverflowError) as exc:
        return ['input must be finite JSON: ' + str(exc)]
    for key in ('request_id', 'object_id', 'object_type'):
        if not text(doc.get(key)) or not known(doc.get(key)):
            errors.append(key + ' must identify the actual review scope')
    if object_types is not None and (not isinstance(doc.get('object_type'), str) or doc['object_type'] not in object_types):
        errors.append('object_type is unsupported for this workflow')
    assessed, cutoff = day(doc.get('as_of')), day(doc.get('knowledge_cutoff'))
    if not assessed or not cutoff or cutoff > assessed:
        errors.append('real YYYY-MM-DD knowledge_cutoff <= as_of required')
    if not isinstance(doc.get('data'), dict):
        errors.append('data must be the workflow-specific object')
    workflow = doc.get('workflow')
    if not isinstance(workflow, dict):
        errors.append('workflow must declare scope, access and responsibility')
        workflow = {}
    context = workflow.get('context')
    if not isinstance(context, dict):
        errors.append('workflow.context is required')
        context = {}
    for key in CONTEXT_KEYS:
        if not text(context.get(key)) or not known(context.get(key)):
            errors.append('workflow.context.' + key + ' required')
    for key in ('object_id', 'object_type'):
        if context.get(key) != doc.get(key):
            errors.append('workflow context differs from native ' + key)
    if workflow.get('as_of') != doc.get('as_of'):
        errors.append('workflow as_of differs from native as_of')
    if not isinstance(workflow.get('role'), str) or workflow['role'] not in ROLES:
        errors.append('explicit supported institutional responsibility required')
    if not isinstance(workflow.get('classification'), str) or workflow['classification'] not in CLASSIFICATIONS:
        errors.append('explicit supported confidentiality classification required')
    allowed = workflow.get('allowed_audiences')
    if not strings(allowed, True) or len(set(allowed or [])) != len(allowed or []):
        errors.append('allowed_audiences must be a distinct nonempty string list')
    if not text(workflow.get('audience')) or not isinstance(allowed, list) or workflow['audience'] not in allowed:
        errors.append('audience must be in the declared allowed_audiences')
    if workflow.get('classification') == 'sar_restricted' and workflow.get('audience') != 'authorized_fiu':
        errors.append('SAR-restricted native results require authorized_fiu audience; external projection unsupported')
    if not strings(workflow.get('unresolved_issues')):
        errors.append('workflow.unresolved_issues must explicitly retain open issues')
    registry = doc.get('sources')
    declared = workflow.get('sources')
    if not records(registry):
        errors.append('sources must be a source-registry list')
        registry = []
    if not records(declared):
        errors.append('workflow.sources must declare source refs and versions')
        declared = []
    if not unique_ids(registry, 'source_ref'):
        errors.append('unique source_ref required for each source record')
    if not unique_ids(declared, 'source_ref'):
        errors.append('distinct workflow source refs required')
    fact_ids = set()
    for index, source in enumerate(registry):
        label = f'sources[{index}]'
        if not text(source.get('version')):
            errors.append(label + '.version required')
        if not day(source.get('received_at')) or not day(source.get('publication_date')):
            errors.append(label + ' needs real publication/receipt dates')
        if 'expires_on' in source and not day(source['expires_on']):
            errors.append(label + '.expires_on must be a real date when supplied')
        if not isinstance(source.get('classification'), str) or source['classification'] not in CLASSIFICATIONS or not _classification_allows(source.get('classification'), workflow.get('classification')):
            errors.append(label + ' classification cannot flow into declared result; mixed restricted sources need a reviewed adapter')
        audiences = source.get('permitted_audiences')
        if not strings(audiences, True) or workflow.get('audience') not in (audiences or []):
            errors.append(label + ' does not permit the declared result audience')
        facts = source.get('facts')
        if not records(facts):
            errors.append(label + '.facts must be a list of fact_id/value/excerpt records')
            continue
        for fact in facts:
            if not text(fact.get('fact_id')) or fact.get('fact_id') in fact_ids:
                errors.append(label + ' fact_id must be globally unique and nonempty')
            else:
                fact_ids.add(fact['fact_id'])
            if 'value' not in fact or not text(fact.get('excerpt')):
                errors.append(label + ' each fact needs a value and supplied excerpt')
    actual = {s.get('source_ref'): s.get('version') for s in registry if text(s.get('source_ref'))}
    projected = {s.get('source_ref'): s.get('version') for s in declared if text(s.get('source_ref'))}
    if actual != projected:
        errors.append('workflow source refs/versions must match the complete detached source registry')
    return errors


def require_valid(doc, validator):
    try:
        evaluated = validator(doc)
        errors = evaluated[0] if isinstance(evaluated, tuple) else evaluated
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, ArithmeticError) as exc:
        raise ValueError('invalid input: ' + str(exc)) from exc
    if not isinstance(errors, list) or not all(isinstance(e, str) for e in errors):
        raise ValueError('validator must return an error list or (errors,warnings)')
    if errors:
        raise ValueError('; '.join(errors))


def source_index(doc):
    return {s['source_ref']: s for s in doc.get('sources', []) if isinstance(s, dict) and text(s.get('source_ref'))}


def evidence_issues(doc, refs, label='evidence'):
    if not strings(refs, True):
        return [label + ': explicit source references required']
    registry = source_index(doc)
    workflow = doc.get('workflow', {})
    declared = {s.get('source_ref'): s.get('version') for s in workflow.get('sources', []) if isinstance(s, dict)}
    cutoff = day(doc.get('knowledge_cutoff'))
    issues = []
    for ref in dict.fromkeys(refs):
        source = registry.get(ref)
        if source is None:
            issues.append(label + ': source not in detached registry: ' + ref)
            continue
        if declared.get(ref) != source.get('version'):
            issues.append(label + ': workflow provenance does not bind source version: ' + ref)
        received, publication = day(source.get('received_at')), day(source.get('publication_date'))
        if not cutoff or not received or not publication or not publication <= received <= cutoff:
            issues.append(label + ': source is future, undated or inconsistently dated: ' + ref)
        expiry = day(source.get('expires_on'))
        if expiry and day(doc.get('as_of')) and expiry < day(doc['as_of']):
            issues.append(label + ': source expired at assessment: ' + ref)
        if workflow.get('audience') not in source.get('permitted_audiences', []):
            issues.append(label + ': recipient is outside supplied source access: ' + ref)
        if not _classification_allows(source.get('classification'), workflow.get('classification')):
            issues.append(label + ': source confidentiality is incompatible: ' + ref)
    return issues


def claim_check(doc, claim, label='claim'):
    if not isinstance(claim, dict) or 'value' not in claim or not known(claim.get('value')):
        return False, [label + ': value is unknown or missing']
    refs, ids = claim.get('source_refs'), claim.get('fact_ids')
    issues = evidence_issues(doc, refs, label)
    if not strings(ids, True) or len(set(ids or [])) != len(ids or []):
        issues.append(label + ': distinct exact fact mappings required')
        return False, issues
    if not strings(refs, True):
        return False, issues
    registry = source_index(doc)
    facts = {f.get('fact_id'): (ref, f) for ref in refs if ref in registry
             for f in registry[ref].get('facts', []) if isinstance(f, dict)}
    supported_refs = set()
    for fact_id in ids:
        found = facts.get(fact_id)
        if found is None:
            issues.append(label + ': fact is not under a cited source: ' + fact_id)
            continue
        ref, fact = found
        supported_refs.add(ref)
        try:
            equal = canonical_hash(fact.get('value')) == canonical_hash(claim['value'])
        except (ValueError, TypeError):
            equal = False
        if not equal:
            issues.append(label + ': supplied value conflicts with fact ' + fact_id)
    if not set(refs).issubset(supported_refs):
        issues.append(label + ': every cited source needs an exact stated fact')
    return not issues, list(dict.fromkeys(issues))


def claim_value(doc, claim, label='claim'):
    supported, issues = claim_check(doc, claim, label)
    return (copy.deepcopy(claim['value']) if supported else None), issues


def claim_bindings(doc):
    """Retain source/fact locators and consistency state without copying raw claims.

    These input paths are evidence locators, not a statement that a domain method
    used every claim or that the stated fact proves a professional conclusion.
    """
    bindings = []
    def visit(value, path):
        if isinstance(value, dict):
            if {'value', 'source_refs', 'fact_ids'}.issubset(value):
                supported, issues = claim_check(doc, value, path)
                bindings.append({'native_input_pointer': path,
                    'source_refs': copy.deepcopy(value['source_refs']),
                    'fact_ids': copy.deepcopy(value['fact_ids']),
                    'consistency': 'exact-supplied-fact' if supported else 'unresolved',
                    'issues': issues})
            else:
                for key, item in value.items():
                    visit(item, path + '/' + key.replace('~', '~0').replace('/', '~1'))
        elif isinstance(value, list):
            for index, item in enumerate(value):
                visit(item, path + '/' + str(index))
    for key, value in doc.items():
        if key not in {'sources', 'workflow'}:
            visit(value, '/' + key.replace('~', '~0').replace('/', '~1'))
    return bindings


def result(doc, skill, method, results, issues=(), limitations=(), handoffs=()):
    require_valid(doc, validate_common)
    if not text(skill) or not text(method) or not isinstance(results, dict):
        raise ValueError('explicit skill, method and domain result object required')
    retained = list(doc['workflow']['unresolved_issues']) + list(issues)
    retained += evidence_issues(doc, list(source_index(doc)), 'source registry')
    if not all(text(issue) for issue in retained):
        raise ValueError('issues must be explicit nonempty strings')
    retained = list(dict.fromkeys(retained))
    output = {'contract_version': VERSION, 'skill': skill, 'method': method,
              'request_id': doc['request_id'], 'object_id': doc['object_id'], 'object_type': doc['object_type'],
              'as_of': doc['as_of'], 'knowledge_cutoff': doc['knowledge_cutoff'],
              'context': copy.deepcopy(doc['workflow']['context']), 'role': doc['workflow']['role'],
              'classification': doc['workflow']['classification'], 'audience': doc['workflow']['audience'],
              'status': 'needs-evidence' if retained else 'draft-for-human-review',
              'results': results, 'unresolved_issues': retained,
              'claim_bindings': claim_bindings(doc),
              'limitations': list(limitations) + ['Supplied source/fact/profile and reviewer identities are not authenticated.',
                  'Exact value mappings establish consistency, not truth or substantive legal sufficiency.',
                  'Professional applicability, acceptance and operational authority remain human-owned.'],
              'source_refs': list(source_index(doc)), 'source_assurance': 'supplied-unverified',
              'handoffs': list(handoffs), 'draft': True, 'human_review_required': True,
              'action_taken': False, 'approval': 'not_requested', 'execution': 'not_performed'}
    return attach_source(output, doc)


def validate_result(output, original_input, compute):
    errors = []
    if original_input is not None:
        try:
            errors += validate_common(original_input)
        except (ValueError, TypeError, KeyError, IndexError, AttributeError) as exc:
            errors.append('invalid original: ' + str(exc))
    validate_reconstruction(output, compute, errors, original_input=original_input)
    return errors


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON object key: ' + key)
        result[key] = value
    return result


def _read(path):
    return json.loads(Path(path).read_text() if path else sys.stdin.read(), object_pairs_hook=_unique_object,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError('non-finite JSON value: ' + value)))


def cli_compute(compute):
    parser = argparse.ArgumentParser()
    parser.add_argument('input', nargs='?')
    args = parser.parse_args()
    try:
        print(json.dumps(compute(_read(args.input)), indent=2, ensure_ascii=False, allow_nan=False))
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, ArithmeticError, OSError) as exc:
        parser.exit(1, str(exc) + '\n')


def cli_input(validate):
    parser = argparse.ArgumentParser()
    parser.add_argument('input', nargs='?')
    args = parser.parse_args()
    try:
        checked = validate(_read(args.input))
        errors = checked[0] if isinstance(checked, tuple) else checked
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, ArithmeticError, OSError) as exc:
        errors = [str(exc)]
    print(json.dumps({'errors': errors}))
    raise SystemExit(bool(errors))


def cli_output(validate):
    parser = argparse.ArgumentParser()
    parser.add_argument('output')
    parser.add_argument('--input', required=True)
    args = parser.parse_args()
    try:
        checked = validate(_read(args.output), _read(args.input))
        errors = checked[0] if isinstance(checked, tuple) else checked
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, ArithmeticError, OSError) as exc:
        errors = [str(exc)]
    print(json.dumps({'errors': errors}))
    raise SystemExit(bool(errors))
