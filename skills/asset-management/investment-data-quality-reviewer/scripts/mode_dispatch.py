"""Explicit, schema-isolated offline mode dispatch; no inferred conversion."""
import importlib
from native_integrity import canonical_hash
MODES = {'data_quality': {'input': 'data_quality_validate_input', 'calculate': 'data_quality_calculate_or_transform', 'output': 'data_quality_validate_output', 'function': 'compute', 'fixture': 'feed_snapshot.json'}, 'vendor_feed': {'input': 'vendor_feed_validate_input', 'calculate': 'vendor_feed_calculate_or_transform', 'output': 'vendor_feed_validate_output', 'function': 'compute', 'fixture': 'feed_reconciliation_example.json'}}

def components(mode):
    if not isinstance(mode,str) or mode not in MODES:raise ValueError('mode must be one of: '+', '.join(MODES))
    spec=MODES[mode]
    return (importlib.import_module(spec['input']),getattr(importlib.import_module(spec['calculate']),spec['function']),importlib.import_module(spec['output']))

def validate_request(doc):
    errors,warnings=[],[]
    try:
        canonical_hash(doc)
        if not isinstance(doc,dict) or set(doc)!={'mode','input'}:raise ValueError('request must contain exactly mode and input')
        if not isinstance(doc['input'],dict):raise ValueError('input must be the selected native input object')
        native,_,_=components(doc['mode'])
        errors,warnings=native.validate(doc['input'])
    except (ValueError,TypeError,KeyError,ArithmeticError,AttributeError) as exc:errors.append('invalid mode request: '+str(exc))
    return errors,warnings
