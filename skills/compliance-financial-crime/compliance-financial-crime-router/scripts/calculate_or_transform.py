"""Return a bounded routing plan; no launch, installation, scheduling or actions."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import sys
from native_integrity import attach_source
from validate_input import validate, routes


def compute(doc):
    errors = validate(doc)
    if errors:
        raise ValueError('; '.join(errors))
    by_id = {r['id']: r for r in routes()}
    known = 'available_skills' in doc
    available = set(doc.get('available_skills', []))
    provided = set(doc.get('provided_data', []))
    plans = []
    action = doc.get('requested_action', 'analyze')
    context = doc.get('context', {})
    missing_context = [k for k in ('institution_id', 'legal_entity_id', 'jurisdiction', 'role')
                       if not isinstance(context.get(k), str) or not context[k].strip() or context[k].lower() in {'unknown', 'n/a'}]
    for intent in doc['intents']:
        route = copy.deepcopy(by_id[intent])
        gaps = []
        for target in [route['primary']] + route['supporting']:
            target['installation'] = 'unknown' if not known else ('listed-installed' if target['name'] in available else 'not-listed')
        if action not in {'analyze', 'draft'}:
            status = 'action_requires_separate_authorization'
            gaps.append('Router does not grant authority or execute the requested ' + action + ' action.')
        elif doc['subject']['type'] not in route['subject_types']:
            status = 'needs_scope_clarification'
            gaps.append('Subject type is incompatible with the declared job.')
        elif missing_context:
            status = 'needs_context'
        elif route['primary']['support_status'] == 'planned':
            status = 'planned_capability_gap'
            gaps.append('Primary workflow is not implemented; supporting skills do not replace it.')
        elif not known:
            status = 'installation_unknown'
        elif route['primary']['name'] not in available:
            status = 'primary_not_installed'
        else:
            status = 'bounded_route'
        gaps.extend('Missing context: ' + k for k in missing_context)
        planned = [s['name'] for s in route['supporting'] if s['support_status'] == 'planned']
        missing = [s['name'] for s in route['supporting'] if s['support_status'] != 'planned' and s['installation'] == 'not-listed']
        if planned:
            gaps.append('Planned supporting methods: ' + ', '.join(planned))
        if missing:
            gaps.append('Uninstalled supporting packages: ' + ', '.join(missing))
        route.update(status=status, unresolved_issues=gaps,
                     data_to_confirm=[x for x in route['required_data'] if x not in provided],
                     primary_owner=route['primary']['name'], launches_skills=False)
        plans.append(route)
    return attach_source({'request_id': doc['request_id'], 'as_of': doc['as_of'],
        'subject': copy.deepcopy(doc['subject']), 'context': copy.deepcopy(context), 'routes': plans,
        'action_taken': False, 'approval': 'not_requested', 'execution': 'not_performed',
        'human_review_required': True, 'professional_acceptance': 'not-established',
        'data_assurance': 'provided_data is a declaration, not verification',
        'standing_note': 'Route selection is not task completion, legal applicability, source authentication or action authority.'}, doc)


if __name__ == '__main__':
    try:
        print(json.dumps(compute(json.loads(Path(sys.argv[1]).read_text())), indent=2, allow_nan=False))
    except (ValueError, OSError, IndexError) as exc:
        print('ERROR', exc, file=sys.stderr); raise SystemExit(1)
