"""Validate the explicitly supplied policy and bounded native input."""
from policy_contract import *
CONFIG_KEYS=('factor_catalog','band_thresholds','band_order','staleness_days','override_max_days','trigger_types_requiring_review')

def validate(doc):
    errors=base_errors(doc,'methodology_version','as_of','config',CONFIG_KEYS)
    if not isinstance(doc,dict) or errors: return errors,[]
    cfg=doc.get('config') or {}; catalog=cfg.get('factor_catalog'); order=cfg.get('band_order'); thresholds=cfg.get('band_thresholds')
    if not isinstance(catalog,dict) or not catalog: errors.append('factor_catalog must be nonempty')
    if not strings(order,True) or len(set(order or []))!=len(order or []): errors.append('unique band_order required')
    elif any('prohibit' in x.lower() for x in order): errors.append('risk bands cannot determine legal prohibition')
    if not records(thresholds) or not thresholds: errors.append('band_thresholds required')
    elif order and ([t.get('band') for t in thresholds]!=order or any(not number(t.get('max_score'),0,100) for t in thresholds)
        or thresholds[-1].get('max_score')!=100 or any(a['max_score']>=b['max_score'] for a,b in zip(thresholds,thresholds[1:]))): errors.append('thresholds must ascend, follow band_order and end at 100')
    for k in ('staleness_days','override_max_days'):
        if not number(cfg.get(k),0): errors.append('invalid '+k)
    if not strings(cfg.get('trigger_types_requiring_review')): errors.append('trigger_types_requiring_review must be supplied')
    if not text(doc.get('customer_id')): errors.append('customer_id required')
    if errors: return errors,[]
    for name,spec in catalog.items():
        if not isinstance(spec,dict): errors.append('factor specification must be object'); continue
        if not number(spec.get('max_weight'),0) or spec.get('max_weight')==0 or not number(spec.get('scale_max'),0) or spec.get('scale_max')==0: errors.append('factor weight and scale must be positive finite numbers')
        if not isinstance(spec.get('required'),bool): errors.append('factor required flag must be explicit')
        if spec.get('floor_at_max') is not None and spec['floor_at_max'] not in order: errors.append('factor floor must be a defined band')
    if all(isinstance(spec,dict) and number(spec.get('max_weight')) for spec in catalog.values()) and not number(sum(spec['max_weight'] for spec in catalog.values())): errors.append('total methodology weight must be finite')
    for key in ('factors','overrides','trigger_events'):
        if not records(doc.get(key,[])): errors.append(key+' must be a list of objects')
    if errors: return errors,[]
    seen=set()
    for f in doc.get('factors',[]):
        name=f.get('factor'); spec=catalog.get(name,{})
        if name not in catalog or name in seen: errors.append('unknown or duplicate factor'); continue
        seen.add(name)
        if not number(f.get('risk_value'),0,spec['scale_max']): errors.append('risk_value outside methodology scale')
        if f.get('weight')!=spec['max_weight']: errors.append('factor weight differs from supplied methodology')
        if 'scale_max' in f and f['scale_max']!=spec['scale_max']: errors.append('factor scale differs from methodology')
        if not text(f.get('source_ref')): errors.append('factor source_ref required')
        if f.get('observed_date') is not None and not day(f['observed_date']): errors.append('invalid factor observed_date')
    record=doc.get('rating_of_record')
    if not isinstance(record,dict) or record.get('band') not in order or not text(record.get('source_ref')): errors.append('rating_of_record with defined band and source_ref required')
    if isinstance(record,dict) and (not day(record.get('effective_date')) or day(record['effective_date'])>day(doc['as_of'])): errors.append('rating_of_record effective_date must be valid and not future')
    for o in doc.get('overrides',[]):
        if o.get('from_band') not in order or o.get('to_band') not in order: errors.append('override bands must be defined')
        for k in ('approved_date','expiry_date'):
            if o.get(k) is not None and not day(o[k]): errors.append('invalid override '+k)
    for e in doc.get('trigger_events',[]):
        if not day(e.get('date')) or day(e['date'])>day(doc['as_of']): errors.append('invalid or future trigger date')
        if not isinstance(e.get('assessed'),bool): errors.append('trigger assessed must be boolean')
        if not text(e.get('source_ref')): errors.append('trigger source_ref required')
    return errors,[]


def main(argv):
    import json, sys
    from pathlib import Path
    p=Path(__file__).resolve().parents[1]/'evals/files/risk_case_example.json' if '--selftest' in argv else Path(argv[0]) if argv else None
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
