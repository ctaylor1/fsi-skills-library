"""AM adapters to generated, pinned shared owner implementations (MIT).

Detached inputs prove reconstruction, never the truth of supplied records.
"""
from copy import deepcopy
from decimal import Context, localcontext
from foundation_contract import date_value, require_sources, validate_common, validate_actual_date
from workflow_foundation import run, check_output

VERSION = 'investment-modernization/1.0'


def shared_review(doc, key, producer, evaluator, validator):
    """Recompute a shared owner's output; bind its evidence to the AM context.

    Every shared source must also exist in the AM registry with the same version
    and as_of. The enclosing source_ref binds the received review record. Same
    object and date are deliberately required; cross-object mappings are not
    supported by this bounded adapter.
    """
    errors = validate_common(doc)
    if errors:
        raise ValueError('; '.join(errors))
    reviews = doc.get('shared_reviews')
    if not isinstance(reviews, dict) or not isinstance(reviews.get(key), dict):
        raise ValueError('shared_reviews.' + key + ' requires detached input and output')
    pair = reviews[key]
    require_sources(doc, [pair.get('source_ref')])
    original, output = pair.get('input'), pair.get('output')
    if not isinstance(original, dict) or not isinstance(output, dict):
        raise ValueError('shared review requires both input and output objects')
    if original.get('context', {}).get('object_id') != doc['object_id'] or original.get('as_of') != doc['as_of']:
        raise ValueError('shared review object/as_of differs from AM request')
    if original.get('data', {}).get('currency') != doc['currency']:
        raise ValueError('shared review currency differs from AM request')
    validate_actual_date(doc, original['as_of'], pair['source_ref'])
    registry = {s['source_ref']: s for s in doc['sources']}
    for source in original.get('sources', []):
        ref = source.get('source_ref')
        require_sources(doc, [ref])
        registered = registry[ref]
        if any(source.get(k) != registered.get(k) for k in ('version', 'as_of')):
            raise ValueError('shared source version/as_of differs from AM registry: ' + ref)
        if date_value(registered['known_at']) > date_value(doc['knowledge_cutoff']):
            raise ValueError('shared evidence was not known at AM cutoff')
    # Preserve the shared owner's native decimal context, even when the AM
    # caller requires exact cash arithmetic. Do not silently change its method.
    with localcontext(Context(prec=28)):
        expected = run(deepcopy(original), producer, evaluator, validator)
        errors = check_output(output, producer, evaluator, validator)
    if errors or output != expected:
        raise ValueError('shared output differs from detached native reconstruction: ' + '; '.join(errors))
    return expected
