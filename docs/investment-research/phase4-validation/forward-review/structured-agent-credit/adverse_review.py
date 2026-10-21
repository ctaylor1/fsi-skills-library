import copy,json,runpy
from pathlib import Path
p=Path('/private/tmp/ir-phase4-structured-forward-credit-20261020')
v=runpy.run_path(str(p/'forward_review.py'))
s,public=v['s'],v['p'];run,save=v['run'],v['save'];checks=[]
def close(actual,expected): assert abs(actual-expected)<1e-9,(actual,expected)
sout=json.loads((p/'sovereign-output.json').read_text()); year=sout['results']['scenario_paths'][0]['years'][0]
for key,expected in {'gdp':2080,'gross_debt':1099.44,'domestic_debt':636.008,'foreign_currency_debt_local':463.432,'interest_expense':43.44,'fx_revaluation':48,'gross_financing_needs':151.24,'debt_to_gdp':1099.44/2080,'debt_stabilizing_primary_balance':84.44,'available_funding_surplus_over_modeled_gfn':3.76}.items():close(year[key],expected)
close(sum(year['debt_ratio_change_components'].values()),1099.44/2080-.5)
assert sout['results']['external_liquidity']['fiscal_availability_established'] is False
checks.append({'case':'sovereign-independent-nominal-and-ratio-bridge','result':'PASS'})
pout=json.loads((p/'public-net-output.json').read_text()); gout=json.loads((p/'public-gross-output.json').read_text())
close(pout['results']['reported_metrics']['illustrative_pledged_revenue_coverage'],85/35)
stress=pout['results']['conditional_scenarios'][0]['metrics']
for key,expected in {'illustrative_pledged_revenue_coverage':10.5/38,'recurring_cash_shortfall':27.5,'cash_shortfall_after_one_time_reserve':2.5,'unfunded_capital_needs':39}.items():close(stress[key],expected)
close(gout['results']['reported_metrics']['illustrative_pledged_revenue_coverage'],230/35)
close(gout['results']['conditional_scenarios'][0]['metrics']['system_operating_cash_after_operating_costs_and_debt_service'],-27.5)
checks.append({'case':'net-vs-gross-pledge-separate-from-system-cash','result':'PASS-numerical; system-deficit-flag-observation-sent-to-author'})
rejects=[]
d=copy.deepcopy(s);d['scenarios'][0]['years'][0]['fiscal_cash_draw']=31;rejects.append(('sovereign-cash-over-capacity','sovereign-credit-researcher',d))
d=copy.deepcopy(s);d['scenarios'][0]['years'][0]['foreign_principal_due_local']=401;rejects.append(('sovereign-maturity-over-opening-bucket','sovereign-credit-researcher',d))
d=copy.deepcopy(s);d['scenarios'][0]['years'][0]['nominal_gdp_growth']=-1;rejects.append(('sovereign-invalid-gdp-denominator','sovereign-credit-researcher',d))
d=copy.deepcopy(s);d['scenarios'][0]['known_at']='2026-10-21T00:00:00Z';rejects.append(('sovereign-future-assumptions','sovereign-credit-researcher',d))
d=copy.deepcopy(s);d['scenarios'][0]['years'][0]['primary_balance']=None;rejects.append(('sovereign-missing-essential-primary-balance','sovereign-credit-researcher',d))
d=copy.deepcopy(public);d['financial_scope']['pledge_basis']='moral-obligation';rejects.append(('public-unsupported-pledge','public-finance-credit-researcher',d))
d=copy.deepcopy(public);d['obligations'][0]['pledged_system_id']='OTHER-SYSTEM';rejects.append(('public-cross-system-direct-obligation','public-finance-credit-researcher',d))
d=copy.deepcopy(public);d['obligations'][0]['period_end']='2024-12-31';rejects.append(('public-wrong-period-obligation','public-finance-credit-researcher',d))
d=copy.deepcopy(public);d['financials']['operating_costs']=None;rejects.append(('public-missing-essential-opex','public-finance-credit-researcher',d))
d=copy.deepcopy(public);d['subject']={'type':'security','id':'NONEXISTENT-SECURITY','issuer_id':'FRESH-WATER'};rejects.append(('public-security-not-in-direct-inventory','public-finance-credit-researcher',d))
for name,skill,doc in rejects:
 path=save(name+'-input',doc);r=run(skill,'validate_input.py',path)
 assert r.returncode!=0 and 'ERROR' in r.stdout and 'Traceback' not in r.stderr,(name,r.stdout,r.stderr)
 checks.append({'case':name,'result':'PASS-rejected'})
for name,skill,source in [('sovereign-rights-denied','sovereign-credit-researcher',s),('public-rights-denied','public-finance-credit-researcher',public)]:
 d=copy.deepcopy(source);d['sources'][0]['permission_status']='denied'; out=v['pipeline'](skill,name,d)
 assert out['results'] is None and out['evidence_refs']==[] and out['source_register']==[]
 checks.append({'case':name,'result':'PASS-withheld'})
for name,skill,source,output in [('sovereign','sovereign-credit-researcher',s,sout),('public','public-finance-credit-researcher',public,pout)]:
 d=copy.deepcopy(output);d.pop('unresolved_issues');path=save(name+'-deleted-output',d);original=save(name+'-retained-original',source)
 r=run(skill,'validate_output.py',path,('--input',original));assert r.returncode!=0 and 'ERROR' in r.stdout
 checks.append({'case':name+'-output-deletion-original-reconstruction','result':'PASS-rejected'})
d=copy.deepcopy(public);d['obligation_inventory_complete']=False;out=v['pipeline']('public-finance-credit-researcher','public-incomplete',d)
assert out['results']['reported_metrics']['illustrative_pledged_revenue_coverage'] is None
checks.append({'case':'public-incomplete-inventory-no-total-coverage','result':'PASS-withheld-total'})
d=copy.deepcopy(s);d['scenarios'][0]['years'][0]['committed_financing']=100;out=v['pipeline']('sovereign-credit-researcher','sovereign-unfunded',d)
close(out['results']['scenario_paths'][0]['years'][0]['uncommitted_funding_gap'],36.24)
assert out['status']=='partial'
checks.append({'case':'sovereign-funding-gap-does-not-disappear-into-conditional-debt-path','result':'PASS-36.24-gap'})
save('independent-checks',checks);save('command-transcripts',v['transcripts'])
print(len(checks),'independent fresh/adverse checks passed')
