"""Fresh arithmetic from raw facts; no package imports or packaged fixtures."""
from pathlib import Path
from decimal import Decimal as D
import json,re
P=Path('/tmp/insurance-p2-forward-life-after-repair')
def out(skill,filename='actual-output.json'):return json.loads((P/skill/filename).read_text())
def verify(skill,checks):
 rows=[]
 for label,actual,expected,raw_anchor,equation in checks:
  ok = D(str(actual)) == D(str(expected))
  rows.append(dict(check=label,actual=str(actual),independent=str(expected),passed=ok,raw_anchor=raw_anchor,equation=equation))
  assert ok,(skill,label,actual,expected)
 (P/skill/'independent-arithmetic.json').write_text(json.dumps(rows,indent=2)+'\n')
s='life-underwriting-reviewer';o=out(s)['results'];ratio=(D('1450000')+D('350000'))/D('90000');verify(s,[('coverage multiple',o['financial_review']['total_coverage_to_income'],ratio,'raw-source.md#application','(1,450,000 + 350,000) / 90,000 = 20')])
s='life-annuity-contract-service-reviewer';o=out(s,'same-day-actual-output.json')['results'];cash=D('50000')-D('3500')+D('1250')-D('2000')-D('4500');after=D('180000')-D('50000');verify(s,[('same-day supplied cash bridge',o['value_scenario']['illustrative_cash_proceeds'],cash,'raw-source.md#terms;raw-source.md#request;same-day-source.md#valuation-confirmation','50,000 - 3,500 + 1,250 - 2,000 - 4,500 = 41,250'),('same-day account value',o['value_scenario']['account_value_after_gross_withdrawal_only'],after,'raw-source.md#request;same-day-source.md#valuation-confirmation','180,000 - 50,000 = 130,000')])
s='life-benefit-claim-reviewer';o=out(s)['results'];net=D('750000')+D('12500')+D('910.25')-D('18300')-D('214.75')-D('5000');verify(s,[('benefit bridge before entitlement',o['benefit_bridge']['illustrative_net_before_entitlement'],net,'raw-source.md#ledger','750,000 + 12,500 + 910.25 - 18,300 - 214.75 - 5,000 = 739,895.50')]);assert o['illustrative_allocation'] is None
s='reinsurance-program-analyzer';o=out(s)['results'];checks=[]
# Independent layer bridge explicitly expands both raw-source program sheets.
# Every tuple is (first-event Q, first-event X, second-event Q, second-event X, fixed, extra).
q_a1=min(D('5000000'),D('8000000'))*D('.2')
x_a1=min(max(D('5000000')-q_a1-D('2000000'),D(0)),D('5000000'))*D('.75')
q_a2=min(D('8000000')*D('.2'),D('3000000')-D('500000')-q_a1)
x_a2=min(min(max(D('10000000')-q_a2-D('2000000'),D(0)),D('5000000'))*D('.75'),D('4000000')-D('1000000')-x_a1)
q_b1=min(D('5000000'),D('8000000'))*D('.25')
x_b1=min(max(D('5000000')-q_b1-D('3000000'),D(0)),D('5000000'))
q_b2=min(D('8000000')*D('.25'),D('4000000')-D('500000')-q_b1)
x_b2=min(min(max(D('10000000')-q_b2-D('3000000'),D(0)),D('5000000')),D('5000000')-x_b1)
expanded={'A':(q_a1,x_a1,q_a2,x_a2,D('1000000'),D('200000')),'B':(q_b1,x_b1,q_b2,x_b2,D('1600000'),D('350000'))}
for c in o['comparisons']:
 p=c['program_id'];anchor='raw-source.md#program-'+p.lower()+';raw-source.md#'+('stress' if c['scenario_id']=='STRESS' else 'zero');v=expanded[p]
 if c['scenario_id']=='STRESS':
  rec=sum(v[:4]);retained=D('15000000')-rec
  for ei in range(2):
   for li in range(2):checks.append((f'{p} stress event {ei+1} layer {li+1}',c['events'][ei]['layers'][li]['illustrative_recoverable'],v[ei*2+li],anchor,'min(event cap after participation, remaining aggregate capacity), applied to remaining loss'))
  checks.extend([(p+' stress recovery',c['illustrative_recoverable'],rec,anchor,'sum of four explicit layer recoveries'),(p+' stress retained',c['retained_loss'],retained,anchor,'15,000,000 - total layer recoveries'),(p+' stress retained plus premium',c['retained_loss_plus_premium'],retained+v[4]+v[5],anchor,'retained + fixed premium + stress extra premium')])
 else:
  checks.extend([(p+' zero recovery',c['illustrative_recoverable'],D(0),anchor,'zero gross loss produces zero recoveries'),(p+' zero cost',c['retained_loss_plus_premium'],v[4],anchor,'zero retained + fixed premium + explicit zero extra premium')])
verify(s,checks)
s='reinsurance-contract-administration-reviewer';o=out(s)['results'];verify(s,[('claim CL-1 break',o['claim_tieouts'][0]['difference'],D('70000')-D('65000'),'raw-source.md#statement;raw-source.md#bordereau','70,000 - 65,000 = 5,000'),('claim CL-2 break',o['claim_tieouts'][1]['difference'],D('60000')-D('65000'),'raw-source.md#statement;raw-source.md#bordereau','60,000 - 65,000 = -5,000'),('closing recoverable',o['recoverable_rollforward']['expected_closing'],D('240000')+D('70000')+D('60000')-D('100000')-D('1250'),'raw-source.md#balances;raw-source.md#statement;raw-source.md#cash;raw-source.md#adjustment','240,000 + 70,000 + 60,000 - 100,000 - 1,250 = 268,750'),('collateral shortfall',o['collateral_comparison']['shortfall'],D('300000')-D('275000'),'raw-source.md#collateral','300,000 - 275,000 = 25,000')])
print('All 26 independent arithmetic comparisons passed; contested benefit allocation remained null.')
