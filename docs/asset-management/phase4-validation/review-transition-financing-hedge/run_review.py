"""Independent reviewer scenarios and arithmetic; no production/source acceptance."""
from pathlib import Path
import json,copy,subprocess,sys
from decimal import Decimal as D
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
results=[]
def fixture(name,file):return json.loads((ROOT/'skills/asset-management'/name/'evals/files'/file).read_text())
def run(name,label,doc,predicate):
 p=HERE/(label+'-input.json');p.write_text(json.dumps(doc,indent=2)+'\n')
 proc=subprocess.run([sys.executable,str(ROOT/'skills/asset-management'/name/'scripts/calculate_or_transform.py'),str(p)],text=True,capture_output=True)
 (HERE/(label+'-observed.txt')).write_text(proc.stdout+proc.stderr)
 output=json.loads(proc.stdout) if proc.returncode==0 else None
 try:passed=predicate(proc.returncode,output)
 except (KeyError,TypeError,IndexError):passed=False
 results.append(dict(case=label,package=name,passed=bool(passed),exit=proc.returncode))
def clean(c,o):return c==0 and not o['unresolved_issues']
def gap(c,o):return c!=0 or bool(o['unresolved_issues'])
n='portfolio-transition-planner';d=fixture(n,'transition.json');d['request_id']='REVIEW-NEW-SCHEDULE';d['initial_settled_cash']='750';d['positions'][0].update(current_settled_quantity='8',target_quantity='3',reference_price='40');d['positions'][1].update(target_quantity='2',reference_price='90');d['proposed_slices'][0].update(quantity='5',estimated_execution_price='42',explicit_cost='3');d['proposed_slices'][1].update(quantity='2',estimated_execution_price='92',explicit_cost='2')
# 750 + 5*42 -3 -2*92 -2 = 771; sell slippage -10 and buy4 => -6, costs5 => -1.
run(n,'transition-new-arithmetic',d,lambda c,o:clean(c,o) and D(o['results']['projected_final_cash'])==771 and D(o['results']['estimated_combined_cost'])==-1)
x=copy.deepcopy(d);x['initial_settled_cash']='101';x['proposed_slices'][1]['settlement_date']='2026-10-06';run(n,'transition-same-day-funding',x,gap)
x=copy.deepcopy(d);x['volume_assumptions'][0]['forecast_market_volume']='40';run(n,'transition-participation',x,gap)
x=copy.deepcopy(d);x['positions'][0]['observed_on']='2026-10-03';run(n,'transition-stale-book',x,lambda c,o:c!=0)
n='securities-financing-reviewer';d=fixture(n,'financing.json');d['request_id']='REVIEW-NEW-FINANCING';d['trades'][0].update(cash_principal='1800',annual_rate='.05');d['agreements'][0]['margin_value']='.1';d['collateral_inventory'][0]['market_value']='2000';d['collateral_allocations'][0]['allocated_market_value']='2000';d['available_funding_cash']='1900'
# 1800*.05*3/360=.75 accrued, 10 days=2.5; haircut credit2000*.9=1800.
run(n,'financing-new-arithmetic',d,lambda c,o:clean(c,o) and D(o['results']['trades'][0]['accrued_amount'])==D('.75') and D(o['results']['trades'][0]['projected_repo_repayment'])==D('1802.5'))
x=copy.deepcopy(d);x['agreements'][0].update(margin_convention='initial-margin',margin_value='1.1');run(n,'financing-different-margin-convention',x,lambda c,o:clean(c,o) and D(o['results']['trades'][0]['required_collateral_market_value'])==1980)
x=copy.deepcopy(d);x['collateral_allocations'][0]['allocated_market_value']='1999.999999999999999999';run(n,'financing-exact-deficiency',x,gap)
x=copy.deepcopy(d);x['trades'][0]['basis_constant_over_interval']=False;run(n,'financing-changing-basis',x,lambda c,o:c!=0)
x=copy.deepcopy(d);y=copy.deepcopy(x['collateral_inventory'][0]);y['collateral_id']='RENAMED';x['collateral_inventory'].append(y);run(n,'financing-duplicate-source-position',x,lambda c,o:c!=0)
n='portfolio-hedge-reviewer';d=fixture(n,'advanced_derivatives.json');d['request_id']='REVIEW-NONLINEAR-RESULT'
# New supplied PV grid, independent expectation: base loss-130, hedge loss-48 =>82 improvement; aftercost-50.
values={'P|base|pv':'700','P|equity-down|pv':'570','H1|base|pv':'711','H1|equity-down|pv':'663'}
for rec in [d['engine_result'],d['independent_benchmark']]:
 for row in rec['values']:
  if row['id'] in values:row['value']=values[row['id']]
run(n,'hedge-new-full-book-grid',d,lambda c,o:clean(c,o) and D(o['results']['comparison'][0]['scenarios'][1]['incremental_pnl_before_cost'])==82 and D(o['results']['comparison'][0]['scenarios'][1]['hedged_book_pnl_after_supplied_cost'])==-50)
x=copy.deepcopy(d);x['engine_request']['input']['books'][0]['positions'][0]['quantity']='11';run(n,'hedge-changed-book-old-result',x,lambda c,o:c!=0)
x=copy.deepcopy(d);x['independent_benchmark']['values'][0]['value']='699';run(n,'hedge-benchmark-miss',x,lambda c,o:gap(c,o) and o['results']['comparison']==[])
x=copy.deepcopy(d);x['engine_result']=None;run(n,'hedge-unavailable-no-fallback',x,lambda c,o:gap(c,o) and o['results']['comparison']==[])
x=copy.deepcopy(d);x['engine_result']['values'].pop();run(n,'hedge-missing-greek',x,lambda c,o:c!=0)
x=copy.deepcopy(d);x['independent_benchmark']['source_ref']='engine-result';run(n,'hedge-same-source-benchmark',x,lambda c,o:c!=0)
report={'scope':'Fresh reviewer numerical scenarios and adverse supplied evidence; no pricing/source/professional acceptance','cases':results,'passed':all(x['passed'] for x in results)}
(HERE/'initial-review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));raise SystemExit(not report['passed'])
