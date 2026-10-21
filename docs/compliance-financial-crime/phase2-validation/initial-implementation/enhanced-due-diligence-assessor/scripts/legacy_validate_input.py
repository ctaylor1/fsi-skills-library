"""Validate the explicitly supplied policy and bounded native input."""
from policy_contract import *

def validate(doc):
    errors=base_errors(doc,'config_version','as_of')
    if not isinstance(doc,dict) or errors: return errors,[]
    for k in ('case_id','template_version','jurisdiction'):
        if not text(doc.get(k)): errors.append(k+' required')
    if not isinstance(doc.get('customer'),dict): errors.append('customer must be an object')
    if not strings(doc.get('required_approvals'),True) or len(set(doc.get('required_approvals') or []))!=len(doc.get('required_approvals') or []): errors.append('required_approvals must be an explicit unique role list')
    ev=doc.get('evidence')
    if not isinstance(ev,dict): errors.append('evidence must be an object')
    else:
        for name,s in ev.items():
            if not isinstance(s,dict): errors.append('evidence section must be object'); continue
            if not isinstance(s.get('present'),bool) or not strings(s.get('items',[])) or not strings(s.get('citations',[])) or not strings(s.get('gaps',[])): errors.append('invalid evidence section '+name)
            if not records(s.get('item_evidence',[])): errors.append('item_evidence must be a list of mappings')
            else:
                for row in s.get('item_evidence',[]):
                    if type(row.get('item_index')) is not int or not text(row.get('source_ref')) or not text(row.get('source_excerpt')): errors.append('item mapping requires integer index, source_ref and source_excerpt')
    if not records(doc.get('recorded_approvals',[])): errors.append('recorded_approvals must be objects')
    rf=doc.get('risk_factors',{})
    if not isinstance(rf,dict): errors.append('risk_factors must be an object')
    else:
        for k in ('sanctions_true_match','sanctions_potential_match'):
            if k in rf and not isinstance(rf[k],bool): errors.append(k+' must be boolean')
    if doc.get('trigger_source_ref') is not None and not text(doc['trigger_source_ref']): errors.append('trigger_source_ref must be a nonempty string')
    roles=[r.get('role') for r in doc.get('recorded_approvals',[]) if isinstance(r,dict)]
    if len(set(str(x) for x in roles))!=len(roles): errors.append('duplicate recorded approval role')
    for r in doc.get('recorded_approvals',[]) if records(doc.get('recorded_approvals',[])) else []:
        if r.get('date') is not None and not day(r['date']): errors.append('invalid approval date')
    return errors,[]


def main(argv):
    import json, sys
    from pathlib import Path
    p=Path(__file__).resolve().parents[1]/'evals/files/edd_case_example.json' if '--selftest' in argv else Path(argv[0]) if argv else None
    try:
        doc=json.loads(p.read_text() if p else sys.stdin.read())
        errors,warnings=validate(doc)
    except (ValueError, TypeError, KeyError, AttributeError) as exc:
        errors,warnings=[str(exc)],[]
    for message in errors: print('ERROR',message)
    for message in warnings: print('WARN',message)
    print(f'input validation: {len(errors)} error(s), {len(warnings)} warning(s)')
    return int(bool(errors))

if __name__=='__main__':
    import sys
    raise SystemExit(main(sys.argv[1:]))
