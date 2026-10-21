"""Validate the explicitly supplied policy and bounded native input."""
from policy_contract import *
CONFIG_KEYS=('ownership_threshold_pct','require_control_prong','min_control_persons','document_required_for_ubo','doc_max_age_days','pct_tolerance','aggregate_across_chains','ownership_test','qualifying_control_types','document_types')

def validate(doc):
    errors=base_errors(doc,'config_version','as_of','config',CONFIG_KEYS)
    if not isinstance(doc,dict) or errors: return errors,[]
    cfg=doc.get('config') or {}
    if cfg.get('ownership_test')!='proportional-equity-gte' or cfg.get('aggregate_across_chains') is not True:
        errors.append('only proportional-equity-gte with aggregation is supported; trusts, voting/control tests and exemptions require specialist review')
    for k,high in (('ownership_threshold_pct',100),('pct_tolerance',100),('doc_max_age_days',None),('min_control_persons',None)):
        if not number(cfg.get(k),0,high): errors.append('invalid config.'+k)
    for k in ('require_control_prong','document_required_for_ubo'):
        if not isinstance(cfg.get(k),bool): errors.append('config.'+k+' must be boolean')
    for k in ('qualifying_control_types','document_types'):
        if not strings(cfg.get(k),True): errors.append('config.'+k+' must be a nonempty string list')
    if not isinstance(cfg.get('min_control_persons'),int) or isinstance(cfg.get('min_control_persons'),bool) or (cfg.get('require_control_prong') and cfg.get('min_control_persons',0)<1): errors.append('min_control_persons must be an integer, positive when required')
    if not text(doc.get('case_id')): errors.append('case_id required')
    for key in ('nodes','ownership_edges','control_edges','declared_ubos','documents'):
        if not records(doc.get(key,[])): errors.append(key+' must be a list of objects')
    if errors: return errors,[]
    nodes=doc.get('nodes',[]); kind={n.get('node_id'):n.get('kind') for n in nodes}
    if not nodes or len(kind)!=len(nodes) or any(not text(k) or v not in ('person','entity') for k,v in kind.items()): errors.append('unique person/entity nodes required')
    root=(doc.get('legal_entity') or {}).get('entity_id')
    if kind.get(root)!='entity': errors.append('legal_entity.entity_id must be an entity node')
    for n in nodes:
        if (n.get('kind')=='entity' and n.get('structure_type')!='corporation') or n.get('structure_type') not in (None,'corporation','individual'): errors.append('unsupported structure_type; route for specialist analysis')
    pairs=set()
    for e in doc.get('ownership_edges',[]):
        pair=(e.get('owner'),e.get('owned'))
        if pair in pairs: errors.append('duplicate ownership edge; combine only under supported scalar equity model')
        pairs.add(pair)
        if e.get('owner') not in kind or kind.get(e.get('owned'))!='entity': errors.append('invalid ownership graph reference')
        if not number(e.get('pct'),0,100) or e.get('pct')==0: errors.append('edge pct must be in (0,100]')
        if not text(e.get('source_ref')): errors.append('ownership edge source_ref required')
    for c in doc.get('control_edges',[]):
        if kind.get(c.get('controller'))!='person' or kind.get(c.get('entity'))!='entity': errors.append('invalid control graph reference')
        if not text(c.get('source_ref')) or not text(c.get('type')): errors.append('control source_ref and type required')
    seen=set()
    for d in doc.get('declared_ubos',[]):
        key=(d.get('person_id'),d.get('basis'))
        if kind.get(d.get('person_id'))!='person' or d.get('basis') not in ('ownership','control') or key in seen: errors.append('invalid or duplicate declared beneficial owner')
        seen.add(key)
        if 'declared_pct' in d and not number(d['declared_pct'],0,100): errors.append('invalid declared_pct')
    ids=set()
    for d in doc.get('documents',[]):
        if not text(d.get('doc_id')) or d['doc_id'] in ids: errors.append('unique doc_id required')
        ids.add(d.get('doc_id'))
        if d.get('subject') not in kind: errors.append('document subject must reference a node')
        if not text(d.get('source_ref')): errors.append('document source_ref required')
        for k in ('issued','expires'):
            if d.get(k) is not None and not day(d[k]): errors.append('invalid document '+k)
    return errors,[]


def main(argv):
    import json, sys
    from pathlib import Path
    p=Path(__file__).resolve().parents[1]/'evals/files/ownership_example.json' if '--selftest' in argv else Path(argv[0]) if argv else None
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
