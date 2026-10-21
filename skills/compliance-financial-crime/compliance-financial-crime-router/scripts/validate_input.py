"""Validate a declared-intent routing request, never infer missing scope."""
from __future__ import annotations
import json
import re
from pathlib import Path
import sys
from datetime import date


def routes():
    return json.loads((Path(__file__).resolve().parents[1] / 'references/routes.json').read_text())['routes']


def validate(doc):
    errors = []
    if not isinstance(doc, dict):
        return ['request must be an object']
    if not isinstance(doc.get('request_id'), str) or not doc['request_id'].strip():
        errors.append('request_id required')
    try:
        if not isinstance(doc.get('as_of'), str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', doc['as_of']):
            raise ValueError('strict date required')
        date.fromisoformat(doc.get('as_of', ''))
    except (ValueError, TypeError):
        errors.append('as_of must be a YYYY-MM-DD date')
    intents = doc.get('intents')
    allowed = {r['id'] for r in routes()}
    if not isinstance(intents, list) or not intents or not all(isinstance(x, str) for x in intents):
        errors.append('intents must be a nonempty list of declared route identifiers')
    elif len(set(intents)) != len(intents) or any(x not in allowed for x in intents):
        errors.append('duplicate or unknown intent; clarify the actual requested job')
    subject = doc.get('subject')
    if not isinstance(subject, dict) or any(not isinstance(subject.get(k), str) or not subject[k].strip() for k in ('id', 'type')):
        errors.append('explicit subject.type and subject.id required')
    if not isinstance(doc.get('context', {}), dict):
        errors.append('context must be an object')
    for key in ('available_skills', 'provided_data'):
        if key in doc and (not isinstance(doc[key], list) or not all(isinstance(x, str) and x.strip() for x in doc[key])):
            errors.append(key + ' must be an explicit string list; omit if unknown')
    if doc.get('requested_action', 'analyze') not in {'analyze', 'draft', 'approve', 'execute', 'send', 'file', 'restrict', 'change_status'}:
        errors.append('unsupported requested_action')
    return errors


if __name__ == '__main__':
    try:
        errors = validate(json.loads(Path(sys.argv[1]).read_text()))
    except (ValueError, OSError, IndexError) as exc:
        errors = [str(exc)]
    for e in errors:
        print('ERROR', e)
    print(f'input validation: {len(errors)} error(s)')
    raise SystemExit(bool(errors))
