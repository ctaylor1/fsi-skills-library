#!/usr/bin/env python3
"""Explicit-intent insurance routing; no NLP, connectors or execution authority."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from insurance_contract import stable_hash, VERSION

REFERENCES = Path(__file__).resolve().parents[1] / 'references'


def route(request):
    if not isinstance(request, dict):
        raise ValueError('request must be an object')
    registry = json.loads((REFERENCES / 'routes.json').read_text())
    aliases = json.loads((REFERENCES / 'migrations.json').read_text())['aliases']
    available = request.get('available_skills')
    if available is not None and (not isinstance(available, list) or
                                  any(not isinstance(x, str) for x in available)):
        raise ValueError('available_skills must be a list of installed skill names')
    intent = request.get('intent')
    if intent is not None and not isinstance(intent, str):
        raise ValueError('intent must be a string')
    for field in ('participant', 'line_of_business', 'legacy_skill', 'requested_action'):
        if field in request and not isinstance(request[field], str):
            raise ValueError(f'{field} must be a string')
    result = dict(contract_version=VERSION, registry_version=registry['version'],
                  request=request, request_hash=stable_hash(request), intent=intent,
                  status='needs-clarification', lead_skill=None, supporting_skills=[],
                  missing_supporting_skills=[], planned_capability=None,
                  missing_context=[], limitations=[], authority_granted=False,
                  target_validation='required',
                  availability='deployment-inventory' if available is not None else 'unverified')
    if request.get('requested_action', 'analyze') not in {'analyze', 'draft'}:
        result.update(status='action-unavailable', limitations=['No insurance action-taking runtime is implemented.'])
        return result
    alias = aliases.get(request.get('legacy_skill'))
    if request.get('legacy_skill') and not alias:
        result['missing_context'] = ['recognized legacy skill or explicit intent']
        return result
    if alias:
        choices = alias['intents']
        if not intent and len(choices) == 1:
            intent = choices[0]
            result['intent'] = intent
        if intent not in choices:
            result['missing_context'] = ['intent: ' + ', '.join(choices)]
            return result
        result['migration'] = {'from': request['legacy_skill'], 'target': alias['target'],
                               'input_compatibility': 'native schema validation required'}
    row = registry['intents'].get(intent)
    if row is None:
        result['missing_context'] = ['supported explicit intent']
        return result
    for field in ('participant', 'line_of_business'):
        allowed = row.get(field)
        if allowed and request.get(field) not in allowed:
            result['missing_context'].append(field + ': ' + ', '.join(allowed))
    if result['missing_context']:
        return result
    # Family intents need domain context before selecting the actual owner.
    if 'variants' in row:
        variant = row['variants'].get(request.get(row['variant_field']))
        if variant is None:
            result['missing_context'] = [row['variant_field'] + ': ' + ', '.join(row['variants'])]
            return result
        row = {**row, **variant}
    result['required_inputs'] = row.get('required_inputs', [])
    if row.get('planned'):
        result.update(status='capability-gap', planned_capability=row['planned'],
                      limitations=[row['limitation']])
        # Evidence tasks cannot masquerade as completing the unavailable job.
        result['evidence_options'] = row.get('evidence_options', [])
        return result
    target = row['target']
    if available is not None and target not in available:
        result.update(status='target-unavailable', limitations=['Target absent from supplied deployment inventory.'])
        return result
    support = row.get('support', [])
    result.update(status='routed', lead_skill=target,
                  supporting_skills=[s for s in support if available is None or s in available],
                  missing_supporting_skills=[s for s in support if available is not None and s not in available],
                  limitations=row.get('limitations', []))
    if row.get('mode'):
        result['target_mode'] = row['mode']
    return result


def validate(output):
    if not isinstance(output, dict) or not isinstance(output.get('request'), dict):
        return ['route must retain its request']
    try:
        expected = route(output['request'])
    except (ValueError, TypeError, KeyError) as exc:
        return [str(exc)]
    return [] if output == expected else ['route differs from retained request and current registry']


def main(argv):
    try:
        checking = bool(argv and argv[0] == '--validate')
        path = argv[1] if checking else argv[0]
        doc = json.loads(Path(path).read_text())
        if checking:
            errors = validate(doc)
            print(f'route validation: {len(errors)} error(s)')
            for error in errors:
                print('ERROR', error)
            return bool(errors)
        print(json.dumps(route(doc), indent=2))
        return 0
    except (IndexError, OSError, ValueError, TypeError, KeyError) as exc:
        print('ERROR', exc, file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
