"""Reproduce a supplied customer-risk methodology without deciding or changing ratings."""
from policy_contract import day, require_valid, limitations
from validate_input import validate
from native_integrity import attach_source

DISCLAIMER='Recommendation and supplied evidence only; human adjudication is required. No risk rating, override, trigger, case, customer decision, or regulatory filing is changed or approved.'

def compute(doc):
    require_valid(doc,validate)
    cfg=doc['config']; catalog=cfg['factor_catalog']; asof=day(doc['as_of']); order=cfg['band_order']
    provided={f['factor']:f for f in doc.get('factors',[])}; findings=[]; details=[]; missing=False
    def add(kind,message,row=None):
        findings.append({'finding_id':f'CRR-F{len(findings)+1:02d}','type':kind,'description':message,
            'evidence':[{'citation':row['source_ref'],'status':'supplied-record'}] if row and row.get('source_ref') else [{'citation':'input:config.factor_catalog','status':'input-field-observation'}]})
    total=0; denominator=sum(s['max_weight'] for s in catalog.values()); floor=None
    for name,spec in catalog.items():
        f=provided.get(name)
        if f is None:
            missing=True
            add('missing_required_factor' if spec['required'] else 'missing_factor','Factor '+name+' is absent; denominator is not reduced.')
            continue
        observed=day(f.get('observed_date'))
        if not observed or observed>asof or (asof-observed).days>cfg['staleness_days']:
            missing=True; add('stale_factor','Factor '+name+' has absent, future, or stale observation date.',f)
        contribution=f['risk_value']/spec['scale_max']*spec['max_weight']; total+=contribution
        details.append({'factor':name,'risk_value':f['risk_value'],'weight':spec['max_weight'],'scale_max':spec['scale_max'],'contribution':round(contribution,6),'citation':f['source_ref']})
        if spec.get('floor_at_max') and f['risk_value']==spec['scale_max']:
            floor=max((x for x in (floor,spec['floor_at_max']) if x),key=order.index)
            add('policy_floor','Supplied policy factor floor: '+spec['floor_at_max']+'. This is not a legal prohibition.',f)
    score=None if missing else round(total/denominator*100,6)
    score_band=next((t['band'] for t in cfg['band_thresholds'] if score is not None and score<=t['max_score']),None)
    band=max((b for b in (score_band,floor) if b),key=order.index) if score is not None else None
    record=doc['rating_of_record']; override_states=[]
    for ov in doc.get('overrides',[]):
        approved,expiry=day(ov.get('approved_date')),day(ov.get('expiry_date'))
        documented=all(ov.get(k) for k in ('approver_role','rationale','source_ref','approval_ref'))
        valid=bool(documented and approved and expiry and approved<=asof<=expiry and 0<=(expiry-approved).days<=cfg['override_max_days'])
        supports=bool(valid and band and ov['from_band']==band and ov['to_band']==record['band'])
        override_states.append({'source_ref':ov.get('source_ref'),'status':'documented-unverified' if valid else 'incomplete-or-expired','supports_record_on_supplied_terms':supports})
        if not valid: add('invalid_override','Override lacks current dates, authority/evidence reference, rationale or permitted duration.',ov)
    if band and band!=record['band']:
        if any(x['supports_record_on_supplied_terms'] for x in override_states): add('documented_override','Supplied override explains the difference; authorization and appropriateness remain for human review.',record)
        else: add('rating_discrepancy','Methodology band differs from the rating of record without a current documented explanation.',record)
    for ev in doc.get('trigger_events',[]):
        if ev.get('type') in cfg['trigger_types_requiring_review'] and (ev.get('assessed') is not True or not ev.get('assessment_ref')):
            add('unassessed_trigger','Trigger requires documented human assessment.',ev)
    kinds={f['type'] for f in findings}
    if kinds&{'invalid_override','unassessed_trigger','documented_override'}: outcome='Escalate-For-Adjudication'
    elif missing: outcome='Remediate-Data-First'
    elif 'rating_discrepancy' in kinds: outcome='Re-Rate-Recommended'
    else: outcome='Align-No-Change'
    return attach_source({'review_id':f"crr-{doc.get('customer_id')}-{doc['as_of']}",'customer_id':doc.get('customer_id'),'as_of':doc['as_of'],
        'methodology_version':doc['methodology_version'],'rating_of_record':record,'score_pct':score,'score_band':score_band,'floor_band':floor,
        'band_thresholds':cfg['band_thresholds'],'band_order':order,'recomputed_band':band,'recommended_band':band,
        'assessment_status':'incomplete' if missing else 'recomputed-from-supplied-policy','factor_detail':details,'findings':findings,'overrides_review':override_states,
        'recommended_review_outcome':outcome,'recommended_next_steps':['Human compliance reviewer assesses data, methodology applicability, overrides and triggers before any rating decision.'],
        'adjudication_required':True,'limitations':limitations()+['No legal prohibition is inferred from a risk score. Policy approval and factor classifications are supplied, not independently verified.'], 'disclaimer':DISCLAIMER},doc)


def main(argv):
    import json,sys
    from pathlib import Path
    p=Path(__file__).resolve().parents[1]/'evals/files/risk_case_example.json' if '--selftest' in argv else Path(argv[0]) if argv else None
    try:
        doc=json.loads(p.read_text() if p else sys.stdin.read())
        print(json.dumps(compute(doc),indent=2,allow_nan=False))
        return 0
    except (ValueError,TypeError,KeyError,AttributeError) as exc:
        print('ERROR',exc,file=sys.stderr)
        return 1

if __name__=='__main__':
    import sys
    raise SystemExit(main(sys.argv[1:]))
