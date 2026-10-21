"""Bounded review of supplied CDD records; no identity or customer determination."""
from policy_contract import day, require_valid, limitations
from legacy_validate_input import validate
from native_integrity import attach_source

DISCLAIMER = 'CDD screening evidence and a recommended review track only; a qualified analyst must adjudicate. No customer decision, identity determination, system action, or filing is performed.'

def compute(doc):
    require_valid(doc,validate)
    cfg=doc['config']; customer=doc['customer']; asof=day(doc['as_of'])
    ctype=customer['customer_type']; docs=doc.get('documents',[]); owners=doc.get('beneficial_owners',[])
    signals=[]; unknown=[]
    def add(name,fire,reason,rows=()):
        signals.append({'signal':name,'fired':bool(fire),'reason':reason,'evidence':list(rows),
                        'evidence_status':'supplied-records','basis':{'policy_version':doc['config_version']}})
    def gap(name,why): unknown.append({'signal':name,'why':why,'status':'unknown'})
    def ref(path): return {'citation':'input:'+path,'evidence_status':'input-field-observation'}
    required=cfg['required_fields_'+ctype]
    missing=[k for k in required if not str(customer.get(k) or '').strip()]
    add('missing_required_field',missing,'Required fields absent: '+', '.join(missing) if missing else 'Required fields supplied.',[ref('customer.'+k) for k in missing])
    reqdocs=cfg['required_documents_'+ctype]
    missingdocs=[t for t in reqdocs if not any(d['type']==t for d in docs)]
    add('missing_required_document',missingdocs,'Required document types absent: '+', '.join(missingdocs) if missingdocs else 'Required document types supplied.',[ref('documents') for t in missingdocs])
    expired=[d for d in docs if d.get('expiry_date') and day(d['expiry_date'])<asof]
    add('expired_document',expired,'Supplied document expiry review.',[{'citation':d['source_ref'],'expiry_date':d['expiry_date']} for d in expired])
    verified=bool(reqdocs) and all(any(d['type']==t and d.get('verified') is True and d not in expired and (not d.get('issue_date') or day(d['issue_date'])<=asof) for d in docs) for t in reqdocs)
    add('unverified_identity',not verified,'Required document verification assertions are incomplete.' if not verified else 'Required document verification assertions supplied; identity assurance is not independently assessed.',[ref('documents')] if not verified else [])
    checks=doc.get('identity_checks',[])
    if not checks: gap('identity_mismatch','No cross-source identity checks supplied.')
    else: add('identity_mismatch',any(c['match'] is False for c in checks),'Supplied cross-source identity comparison.',[{'citation':c['source_ref'],'attribute':c.get('attribute')} for c in checks if c['match'] is False])
    if not customer.get('country'): gap('high_risk_jurisdiction','Customer country missing.')
    else:
        hr={s.upper() for s in cfg['high_risk_countries']}; rows=[]
        if customer['country'].upper() in hr: rows.append(ref('customer.country'))
        for owner in owners:
            if not owner.get('country'): gap('high_risk_jurisdiction','Owner country missing.')
            elif owner['country'].upper() in hr: rows.append({'citation':owner['source_ref']})
        add('high_risk_jurisdiction',rows,'Comparison to the supplied policy country list only.',rows)
    if ctype=='entity':
        if not customer.get('industry'): gap('high_risk_industry','Industry missing.')
        else:
            fire=customer['industry'].lower() in {s.lower() for s in cfg['high_risk_industries']}
            add('high_risk_industry',fire,'Comparison to the supplied policy industry list only.',[ref('customer.industry')] if fire else [])
    names={'pep':'pep_flag','sanctions':'sanctions_potential_match','adverse_media':'adverse_media_flag'}
    for kind,signal in names.items():
        hits=doc.get('screening_hits',{}).get(kind)
        coverage=doc.get('screening_coverage',{}).get(kind,{})
        observed=day(coverage.get('as_of'))
        complete=(coverage.get('status')=='complete' and observed is not None and 0<=(asof-observed).days<=cfg['screening_max_age_days'] and bool(coverage.get('source_ref')))
        if hits is None or not complete: gap(signal,'Current search coverage with supplied source reference is incomplete or absent.')
        if hits is not None:
            add(signal,bool(hits),'Potential indicator in supplied screening results; human identity/status review required.' if hits else 'No indicator in supplied results; absence is limited to documented search coverage.',[{'citation':h['source_ref'],'party':h.get('party')} for h in hits])
    if ctype=='entity':
        if not owners:
            gap('beneficial_ownership','No ownership records supplied; no beneficial-ownership conclusion.')
        else:
            total=sum(o['ownership_pct'] for o in owners)
            ev=[{'citation':o['source_ref'],'ownership_pct':o['ownership_pct']} for o in owners]
            add('ownership_over_100',total>100,'Declared scalar percentages sum to '+str(total)+'.',ev if total>100 else [])
            add('ubo_below_coverage',total<cfg['ubo_coverage_target_pct'],'Policy coverage screen only; this does not identify legal beneficial owners.',ev if total<cfg['ubo_coverage_target_pct'] else [])
            unverified=[o for o in owners if o['ownership_pct']>=cfg['ubo_threshold_pct'] and o.get('verified') is not True]
            add('ubo_unverified',unverified,'Ownership verification assertions incomplete for policy threshold candidates.',[{'citation':o['source_ref']} for o in unverified])
    fired=[s['signal'] for s in signals if s['fired']]
    if 'sanctions_potential_match' in fired: track='Escalate-For-Adjudication'
    elif unknown: track='Needs-Data'
    elif set(fired)&set(cfg['edd_signals']): track='EDD-Recommended'
    elif fired: track='Remediate-First'
    else: track='Standard-CDD'
    steps=['Human analyst reviews all supplied assertions and limitations before any customer decision.']
    if unknown: steps.append('Obtain missing evidence and current search coverage before concluding the assessment.')
    if 'sanctions_potential_match' in fired: steps.append('Route the potential sanctions match to sanctions-match-investigator.')
    if 'pep_flag' in fired: steps.append('Route PEP identity and risk review to the CDD/EDD analyst; PEP status alone is not sanctions status.')
    if 'adverse_media_flag' in fired: steps.append('Route media relevance and identity review to adverse-media-investigator.')
    return attach_source({'screening_id':f"cdd-{doc['case_id']}-{doc['as_of']}",'case_id':doc['case_id'],'as_of':doc['as_of'],
        'config_version':doc['config_version'],'customer':{k:customer.get(k) for k in ('customer_id','customer_type','legal_name','country')},
        'signals':signals,'fired_signals':fired,'not_evaluable':unknown,'recommended_track':track,
        'adjudication_required':True,'recommended_next_steps':steps,'limitations':limitations()+['Onboarding evidence screening only; periodic review orchestration, digital-ID assurance, and legal beneficial-ownership analysis are not implemented.'],
        'disclaimer':DISCLAIMER},doc)


def main(argv):
    import json,sys
    from pathlib import Path
    p=Path(__file__).resolve().parents[1]/'evals/files/case_example.json' if '--selftest' in argv else Path(argv[0]) if argv else None
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
