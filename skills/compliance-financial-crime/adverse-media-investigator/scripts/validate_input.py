"""Validate the explicitly supplied policy and bounded native input."""
from policy_contract import *
CONFIG_KEYS=('category_weight','assertion_addend','source_tier_addend','recency','material_min','watch_min','coverage_max_age_days')

def validate(doc):
    errors=base_errors(doc,'config_version','as_of_date','scoring_config',CONFIG_KEYS)
    if not isinstance(doc,dict) or errors: return errors,[]
    cfg=doc.get('scoring_config') or {}
    for k in ('category_weight','assertion_addend','source_tier_addend','recency'):
        if not isinstance(cfg.get(k),dict) or not cfg[k] or any(not number(v) for v in cfg[k].values()): errors.append('invalid scoring_config.'+k)
    if not number(cfg.get('material_min'),0) or not number(cfg.get('watch_min'),0) or cfg.get('material_min',0)<=cfg.get('watch_min',0): errors.append('material_min must exceed nonnegative watch_min')
    if not number(cfg.get('coverage_max_age_days')): errors.append('coverage_max_age_days required')
    if errors: return errors,[]
    if not {'finding','allegation','resolved-dismissed'}<=set(cfg['assertion_addend']): errors.append('assertion scoring incomplete')
    if not {'1','2','3'}<=set(cfg['source_tier_addend']): errors.append('source tier scoring incomplete')
    if not {'within_2y_days','within_5y_days','within_2y','within_5y','older'}<=set(cfg['recency']): errors.append('recency scoring incomplete')
    rec=cfg['recency']
    if all(k in rec for k in ('within_2y_days','within_5y_days')) and rec['within_2y_days']>=rec['within_5y_days']: errors.append('recency windows must ascend')
    if not records(doc.get('subjects')) or not doc.get('subjects'): errors.append('subjects must be nonempty object list'); return errors,[]
    seen=set()
    for s in doc['subjects']:
        sid=s.get('subject_id')
        if not text(sid) or sid in seen or not text(s.get('name')) or s.get('type') not in ('person','entity'): errors.append('unique subject id, name and person/entity type required')
        seen.add(sid)
        if not records(s.get('hits',[])): errors.append('hits must be objects'); continue
        if not strings(s.get('aliases',[])): errors.append('aliases must be strings')
        if not strings(s.get('known_identifiers',[])): errors.append('known_identifiers must be strings')
        if s.get('dob') is not None and not day(s['dob']): errors.append('invalid subject dob')
        coverage=s.get('search_coverage',{})
        if not isinstance(coverage,dict): errors.append('search_coverage must be an object')
        elif any(k in coverage and not strings(coverage[k]) for k in ('sources','queries','languages')): errors.append('coverage sources, queries and languages must be string lists')
        hids=set()
        for h in s.get('hits',[]):
            for k in ('hit_id','source','source_ref','headline','excerpt'):
                if not text(h.get(k)): errors.append('hit '+k+' required')
            if h.get('hit_id') in hids: errors.append('duplicate hit id')
            hids.add(h.get('hit_id'))
            if type(h.get('source_tier')) is not int or h.get('source_tier') not in (1,2,3): errors.append('explicit source_tier 1, 2 or 3 required')
            if h.get('category') not in cfg['category_weight']: errors.append('category absent from supplied policy')
            if h.get('assertion_type') not in ('finding','allegation','resolved-dismissed'): errors.append('unknown assertion type')
            if h.get('list_type') not in (None,'sanctions','pep'): errors.append('unknown list type')
            if not records(h.get('match_evidence',[])): errors.append('match_evidence must be object list')
            if not strings(h.get('supersedes_hit_ids',[])): errors.append('supersedes_hit_ids must be string list')
        for h in s.get('hits',[]):
            if any(i not in hids or i==h.get('hit_id') for i in h.get('supersedes_hit_ids',[])): errors.append('supersession must reference other supplied hits')
    return errors,[]


def main(argv):
    import json, sys
    from pathlib import Path
    p=Path(__file__).resolve().parents[1]/'evals/files/screening_batch_example.json' if '--selftest' in argv else Path(argv[0]) if argv else None
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
