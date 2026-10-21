from build_review import *
import math

def build_surveillance():
    refs=[ref('surveillance-prior-financials','user-facts:2025-nine-month-financials-and-liquidity'),ref('surveillance-current-financials','user-facts:2026-nine-month-financials-and-liquidity'),ref('prior-OAS','user-facts:OAS-2026-10-19T18Z'),ref('current-OAS','user-facts:OAS-2026-10-20T18Z')]
    d=base('independent-forward-surveillance-base',[source('surveillance-prior-financials','financial_statement'),source('surveillance-current-financials','financial_statement'),source('prior-OAS','market_data','2026-10-19T19:00:00Z'),source('current-OAS','market_data','2026-10-20T19:00:00Z')],refs)
    d['issuer_profile']='nonfinancial-corporate'
    d['prior']={**context(2025),'ebitda':110,'gross_debt':550,'unrestricted_cash':55,'interest_expense':14,'mandatory_capex':20,'available_committed_facilities':30,'near_term_maturities':75,'maturity_inventory_complete':True,'evidence_refs':[refs[0]]}
    d['current']={**context(2026),'ebitda':90,'gross_debt':585,'unrestricted_cash':45,'interest_expense':15,'mandatory_capex':24,'available_committed_facilities':35,'near_term_maturities':90,'maturity_inventory_complete':True,'evidence_refs':[refs[1]]}
    d['thresholds']={'leverage_increase_x':0.25,'coverage_decline_x':0.25,'spread_widening_bps':50}
    d['events']=[]
    d['prior_spread']={'security_id':SECURITY,'currency':'USD','basis':'OAS-supplied','spread_bps':100,'evidence_refs':[refs[2]],'observed_at':'2026-10-19T18:00:00Z'}
    d['current_spread']={'security_id':SECURITY,'currency':'USD','basis':'OAS-supplied','spread_bps':155,'evidence_refs':[refs[3]],'observed_at':'2026-10-20T18:00:00Z'}
    d['spread_freshness_policy']={'max_current_age_hours':8}
    return d

def surveillance_main():
    skill='issuer-credit-surveillance-reviewer';snapshot(skill);d=build_surveillance()
    results=[run_case(skill,'base',d,lambda x:x['results'].update(spread_change_bps=54))]
    variants={}
    x=copy.deepcopy(d);del x['current_spread']['observed_at'];variants['missing-observation-time']=x
    x=copy.deepcopy(d);del x['spread_freshness_policy'];variants['missing-freshness-policy']=x
    x=copy.deepcopy(d);x['current_spread']['observed_at']='2026-10-20T13:59:59Z';variants['stale-one-second-over-8h']=x
    x=copy.deepcopy(d);x['current_spread']['observed_at']='2026-10-20T14:00:00Z';variants['exact-8h-boundary']=x
    x=copy.deepcopy(d);x['spread_freshness_policy']['max_current_age_hours']=0;variants['zero-policy-with-4h-old-current']=x
    x=copy.deepcopy(d);x['spread_freshness_policy']['max_current_age_hours']=0;x['current_spread']['observed_at']='2026-10-20T22:00:00Z';x['sources'][3]['known_at']='2026-10-20T22:00:00Z';variants['zero-policy-observed-and-known-at-cutoff']=x
    x=copy.deepcopy(d);x['current_spread']['observed_at']='2026-10-20T22:00:01Z';variants['observation-one-second-after-cutoff']=x
    x=copy.deepcopy(d);x['as_of']='2026-10-19';variants['observation-after-economic-asof']=x
    x=copy.deepcopy(d);x['sources'][3]['known_at']='2026-10-20T17:59:59Z';variants['source-version-known-before-observation']=x
    x=copy.deepcopy(d);x['sources'][3]['known_at']='2026-10-20';variants['date-only-source-knowledge']=x
    x=copy.deepcopy(d);x['current_spread']['observed_at']='2026-10-19T18:00:00Z';variants['unordered-equal-observation-instants']=x
    x=copy.deepcopy(d);x['current_spread']['observed_at']='2026-10-20T18:00:00';variants['naive-observation-time']=x
    x=copy.deepcopy(d);x['spread_freshness_policy']['max_current_age_hours']=-1;variants['negative-freshness-policy']=x
    x=copy.deepcopy(d);x['current_spread']['observed_at']='2026-10-20T14:00:00-04:00';x['prior_spread']['observed_at']='2026-10-19T14:00:00-04:00';variants['timezone-equivalent-instant']=x
    x=copy.deepcopy(d);x['current_spread']['basis']='Z-spread-supplied';variants['spread-basis-mismatch']=x
    x=copy.deepcopy(d);x['current']['maturity_inventory_complete']=False;variants['incomplete-current-maturity-inventory']=x
    x=copy.deepcopy(d);x['current']['period']['end']='2026-12-31';variants['future-reported-financial-period']=x
    x=copy.deepcopy(d);x['prior']['period']['start']='2025-04-01';variants['incomparable-financial-period-duration']=x
    x=copy.deepcopy(d);x['current']['interest_expense']=0;variants['zero-interest-expense']=x
    x=copy.deepcopy(d);x['current_spread']['security_id']='UNRELATED-ISSUER-NOTE';x['prior_spread']['security_id']='UNRELATED-ISSUER-NOTE';variants['matching-quotes-unbound-security-identity']=x
    x=copy.deepcopy(d);x['sources'][2]['kind']='financial_statement';x['sources'][3]['kind']='financial_statement';variants['quote-citations-wrong-source-kind']=x
    x=copy.deepcopy(d);x['current_spread']['spread_bps']=150;variants['exact-50bps-alert-boundary']=x
    for name,doc in variants.items():
        doc['request_id']='independent-forward-surveillance-'+name
        results.append(run_case(skill,name,doc))
    prior={'gross_leverage_x':Fraction(550,110),'net_leverage_x':Fraction(550-55,110),'interest_coverage_x':Fraction(110,14),'fixed_charge_proxy_x':Fraction(110-20,14),'liquidity_to_known_maturity_x':Fraction(55+30,75)}
    current={'gross_leverage_x':Fraction(585,90),'net_leverage_x':Fraction(585-45,90),'interest_coverage_x':Fraction(90,15),'fixed_charge_proxy_x':Fraction(90-24,15),'liquidity_to_known_maturity_x':Fraction(45+35,90)}
    expected={'prior':{k:str(v) for k,v in prior.items()},'current':{k:str(v) for k,v in current.items()},'changes':{k:str(current[k]-v) for k,v in prior.items()},'spread_change_bps':155-100,'current_quote_age_hours':4,'prior_quote_age_hours':28,'prior_quote_age_not_subject_to_current_age_policy':True,'expected_alerts':['net leverage increased beyond supplied threshold','interest coverage declined beyond supplied threshold','spread widened beyond supplied threshold']}
    dump(OUT/'independent-surveillance-expectations.json',expected)
    by={r['case']:r for r in results};baseout=by['base']['output']['results'];checks=[]
    for period,exp in [('prior',prior),('current',current)]:
        for k,v in exp.items():checks.append({'check':period+' '+k,'actual':baseout['period_metrics'][period][k],'expected_exact':str(v),'pass':math.isclose(baseout['period_metrics'][period][k],float(v),rel_tol=1e-12,abs_tol=1e-12)})
    for k,v in prior.items():
        diff=current[k]-v;actual=baseout['metric_changes'][k]
        checks.append({'check':'change '+k,'actual':actual,'expected_exact':str(diff),'pass':math.isclose(actual,float(diff),rel_tol=1e-12,abs_tol=1e-12)})
    checks.append({'check':'base spread difference and all 3 supplied-threshold alerts','pass':baseout['spread_change_bps']==55 and baseout['alerts']==expected['expected_alerts']})
    checks.append({'check':'tampered spread output rejected with detached original','pass':by['base']['stages']['validate_tampered_output']==1})
    for name in ('missing-observation-time','missing-freshness-policy','stale-one-second-over-8h','zero-policy-with-4h-old-current','observation-one-second-after-cutoff','observation-after-economic-asof','source-version-known-before-observation','unordered-equal-observation-instants','spread-basis-mismatch'):
        out=by[name]['output'];r=out['results']
        checks.append({'check':name+' withholds spread and its alert while retaining finance','pass':r is not None and r['spread_change_bps'] is None and 'spread widened beyond supplied threshold' not in r['alerts'] and r['period_metrics']['current']['net_leverage_x']==6})
    for name in ('exact-8h-boundary','zero-policy-observed-and-known-at-cutoff','timezone-equivalent-instant'):
        r=by[name]['output']['results'];checks.append({'check':name+' accepts eligible spread','pass':r['spread_change_bps']==55 and 'spread widened beyond supplied threshold' in r['alerts']})
    for name in ('naive-observation-time','negative-freshness-policy','future-reported-financial-period','incomparable-financial-period-duration'):
        checks.append({'check':name+' controlled input/calculation rejection','pass':by[name]['stages']['validate_input']==1 and by[name]['stages']['calculate']==1})
    r=by['date-only-source-knowledge']['output'];checks.append({'check':'date-only source precision withholds entire source-gated projection','pass':r['results'] is None and r['calculation_lineage']==[] and r['evidence_refs']==[]})
    r=by['incomplete-current-maturity-inventory']['output']['results'];checks.append({'check':'incomplete maturity inventory withholds liquidity ratio and change','pass':r['period_metrics']['current']['liquidity_to_known_maturity_x'] is None and r['metric_changes']['liquidity_to_known_maturity_x'] is None and r['period_metrics']['current']['net_leverage_x']==6})
    r=by['zero-interest-expense']['output']['results'];checks.append({'check':'zero interest withholds coverage/proxy and coverage alert','pass':r['period_metrics']['current']['interest_coverage_x'] is None and r['period_metrics']['current']['fixed_charge_proxy_x'] is None and 'interest coverage declined beyond supplied threshold' not in r['alerts']})
    r=by['exact-50bps-alert-boundary']['output']['results'];checks.append({'check':'50bps exact-threshold comparison is inclusive','pass':r['spread_change_bps']==50 and 'spread widened beyond supplied threshold' in r['alerts']})
    dump(OUT/'surveillance-independent-checks.json',checks)
    dump(OUT/'surveillance-case-summary.json',[{k:v for k,v in r.items() if k!='output'} for r in results])
    print(json.dumps({'surveillance_cases':len(results),'independent_checks':len(checks),'failed_checks':[c for c in checks if not c['pass']],'manifest_failures':json.loads((OUT/'provenance'/(skill+'.json')).read_text())['manifest_failures']},indent=2))

if __name__=='__main__':surveillance_main()
