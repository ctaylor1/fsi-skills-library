"""Independent fresh private-fund and institutional source-bound examples."""
import copy,json,subprocess,sys
from decimal import Decimal
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).resolve().parent
REF={'source_ref':'independent-synthetic-record'}
BASE={'request_id':'INDEPENDENT-PHASE4','object_id':'SYNTHETIC-ALPHA','as_of':'2026-10-04','knowledge_cutoff':'2026-10-04','currency':'USD','audience':'internal-review','sources':[{'source_ref':'independent-synthetic-record','version':'1','as_of':'2026-10-04','known_at':'2026-10-04','locator':'Synthetic fresh reviewer-created source records; no institution or legal authority'}],'unresolved_issues':[]}
fin=copy.deepcopy(BASE);fin.update(mode='subscription',inventory_complete=True,inventory_source_ref=REF['source_ref'])
fin['agreement']={'version':'A1','reviewed_by':'synthetic-finance-owner','effective_from':'2026-01-01','expires':'2027-10-05','currency':'USD','facility_type':'subscription','concentration_method':'fixed-pre-cap-credit-base','proceeds_assumption':'working capital pending supplied investor calls','permitted_proceeds':['working-capital'],'maximum_facility_debt':'80','maximum_fund_debt_to_nav':'0.4',**REF}
fin['facility']={'id':'FACILITY-A','agreement_version':'A1','maturity_date':'2027-10-05','proposed_draw_date':'2026-10-05','proceeds_use':'working-capital','cost_assumption':'constant pro forma draw for365 days, no resets','commitment_limit':'100','outstanding':'30','proposed_draw':'10','letters_of_credit':'5','reserves':'5','other_fund_debt':'10','upfront_fee':'1','fund_nav':'200','interest_rate':'0.10','undrawn_fee_rate':'0.01','accrual_days':365,'day_basis':365,'total_uncalled_commitments':'200',**REF}
fin['collateral']=[{'id':id,'agreement_version':'A1','currency':'USD','concentration_group':group,'eligible':True,'eligibility_reason':'supplied agreement-approved investor','haircut':haircut,'advance_rate':'0.8','uncalled_commitment':'100',**REF} for id,group,haircut in [('LP-A','A','0'),('LP-B','B','0.5')]]
fin['concentration_limits']=[{'group':group,'agreement_version':'A1','maximum_fraction':'0.5',**REF} for group in ['A','B']]
sec=copy.deepcopy(BASE);sec.update(mode='lp-led-secondary',flow_inventory_complete=True,inventory_source_ref=REF['source_ref'])
sec['transaction']={'id':'LP-INTEREST-SALE','version':'T1','reviewed_by':'synthetic-transaction-owner','currency':'USD','nav_date':'2026-09-01','materials_received_on':'2026-10-01','decision_deadline':'2026-10-20','settlement_date':'2026-10-25','pricing_convention':'reference-nav-plus-calls-minus-distributions','conflicts_owner':'conflict-reviewer','minimum_review_days':14,'reference_nav':'200','existing_management_fee_rate':'0.02','existing_carried_interest_rate':'0.20',**REF}
sec['interim_flows']=[{'id':id,'kind':kind,'date':day,'currency':'USD','transaction_version':'T1','amount':amount,**REF} for id,kind,day,amount in [('CALL-1','capital-call','2026-09-10','20'),('DIST-1','distribution','2026-09-20','10')]]
sec['conflicts']=[]
sec['options']=[{'id':'SELL-HALF','transaction_version':'T1','currency':'USD','side_letter_treatment':'preserved','fee_carry_basis':'reviewed allocated amounts for half-interest option','price_to_reference_nav':'0.9','cash_fees':'2','cash_crystallized_carry':'3','new_management_fee_rate':'0.02','new_carried_interest_rate':'0.20','status_quo_claimed':False,'sale_fraction':'0.5',**REF}]
gp=copy.deepcopy(sec);gp['mode']='gp-led-continuation';o=gp['options'][0];o.pop('sale_fraction');o.update(id='ROLL-SIXTY',roll_fraction='0.6',roll_fees='4',roll_crystallized_carry='6',upfront_new_capital='5',new_uncalled_commitment='30',new_management_fee_rate='0.015',new_carried_interest_rate='0.15')
inst=copy.deepcopy(BASE);inst.update(extension='liability-real-assets',opening_cash='50',inventory_complete=True,inventory_source_ref=REF['source_ref'])
inst['policy']={'version':'P1','reviewed_by':'synthetic-ALM-owner','objective':'test supplied dated payments against portfolio and real-asset cash assumptions','currency':'USD','effective_from':'2026-01-01','expires':'2027-12-31','discount_basis':'supplied-factors-by-dated-liability','maximum_illiquid_fraction':'0.4','maximum_valuation_age_days':30,'parallel_shift_bps':'100',**REF}
inst['liability_cashflows']=[{'id':id,'due_date':day,'amount':'100','liability_basis':'provided institution projection, not actuarially calculated','currency':'USD',**REF} for id,day in [('L1','2026-10-31'),('L2','2026-11-30')]]
inst['discount_factors']=[{'id':'FACTOR-'+id,'liability_id':id,'due_date':day,'policy_version':'P1','base_factor':base,'down_factor':down,'up_factor':up,'currency':'USD',**REF} for id,day,base,down,up in [('L1','2026-10-31','0.98','0.99','0.97'),('L2','2026-11-30','0.96','0.98','0.94')]]
inst['assets']=[{'id':id,'market_value':value,'asset_class':kind,'illiquid':illiquid,'real_asset':illiquid,'valuation_date':'2026-10-04','valuation_basis':'supplied current independent valuation','earliest_liquidation_date':'2026-10-31' if not illiquid else '2027-12-31','liquidation_fraction':'1','currency':'USD',**REF} for id,value,kind,illiquid in [('BOND','150','fixed-income',False),('INFRA','100','infrastructure',True)]]
inst['asset_cashflows']=[{'id':id,'asset_id':asset,'date':day,'kind':kind,'amount':value,'currency':'USD',**REF} for id,asset,day,kind,value in [('BOND1','BOND','2026-10-31','principal','50'),('BOND2','BOND','2026-11-30','principal','100'),('INFRA1','INFRA','2026-10-31','distribution','10'),('INFRA2','INFRA','2026-11-30','distribution','10')]]
inst['scenarios']=[{'id':scenario,'policy_version':'P1','discount_case':case,'liability_multiplier':'1','currency':'USD','asset_shocks':[{'asset_id':'BOND','price_return':'0','cashflow_multiplier':'1','delay_days':0,**REF},{'asset_id':'INFRA','price_return':price,'cashflow_multiplier':cash,'delay_days':delay,**REF}],**REF} for scenario,case,price,cash,delay in [('BASE','base','0','1',0),('INFRA-DOWNSIDE','down','-0.5','0.5',30)]]

results=[]
def save(name,value):(OUT/(name+'.json')).write_text(json.dumps(value,indent=2)+'\n')
def execute(skill,name,request):
 save(name+'-request',request);package=ROOT/'skills/asset-management'/skill
 p=subprocess.run([sys.executable,'-B',str(package/'scripts/calculate_or_transform.py'),str(OUT/(name+'-request.json'))],capture_output=True,text=True)
 if p.returncode:
  (OUT/(name+'-output.json')).unlink(missing_ok=True)
  return {'exit':p.returncode,'stderr':p.stderr.strip()}
 output=json.loads(p.stdout);save(name+'-output',output)
 validation=subprocess.run([sys.executable,'-B',str(package/'scripts/validate_output.py'),str(OUT/(name+'-output.json')),'--input',str(OUT/(name+'-request.json'))],capture_output=True,text=True)
 return {'exit':0,'output':output,'output_validation_exit':validation.returncode}
def trial(skill,name,request,expectation,check):
 r=execute(skill,name,request);record={'skill':skill,'case':name,'expectation':expectation,'passed':bool(check(r)),'exit':r['exit']}
 if r['exit']==0:record.update(results=r['output']['results'],issues=r['output']['unresolved_issues'],output_validation_exit=r['output_validation_exit'])
 else:record['stderr']=r['stderr']
 results.append(record)
def metric(r,key):return Decimal(r['output']['results'][key])
fskill='private-fund-financing-reviewer';sskill='private-fund-restructuring-reviewer';iskill='institutional-investment-solutions-planner'
trial(fskill,'subscription-base',fin,'Raw commitments200, pre-cap credit120, capped base100, usage50, draw headroom50, fund debt50/leverage.25/headroom30, period interest4/fee.55/upfront1 total5.55.',lambda r:r['exit']==0 and r['output_validation_exit']==0 and all(metric(r,k)==Decimal(v) for k,v in [('pre_cap_credit','120'),('borrowing_base','100'),('draw_headroom','50'),('fund_debt','50'),('fund_debt_to_nav','.25'),('leverage_headroom','30'),('interest_cost','4'),('undrawn_fee_cost','.55'),('total_period_cost','5.55')]))
v=copy.deepcopy(fin);v['mode']='nav';v['agreement']['facility_type']='nav';v['facility'].pop('total_uncalled_commitments')
for c in v['collateral']:c['nav']=c.pop('uncalled_commitment')
trial(fskill,'nav-base',v,'Same supplied collateral math on NAV base, with mode-bound source fields.',lambda r:r['exit']==0 and metric(r,'borrowing_base')==100)
v=copy.deepcopy(fin);v['inventory_complete']=False
trial(fskill,'financing-incomplete',v,'Incomplete collateral inventory withholds borrowing base and dependent draw headroom.',lambda r:r['exit']==0 and r['output']['results']['borrowing_base'] is None and r['output']['results']['draw_headroom'] is None)
v=copy.deepcopy(fin);v['facility']['proposed_draw']='40.000000000001';v['agreement']['maximum_fund_debt_to_nav']='0.4'
trial(fskill,'exact-leverage-breach',v,'Debt80.000000000001 exceeds NAV200*.4 despite displayed leverage rounding to.4.',lambda r:r['exit']==0 and metric(r,'leverage_headroom')<0 and bool(r['output']['unresolved_issues']))
v=copy.deepcopy(fin);v['agreement']['expires']='2026-11-01';v['facility']['proposed_draw_date']='2026-12-01'
trial(fskill,'draw-after-agreement-expiry',v,'A proposed draw after the supplied agreement expires cannot receive an issue-free credit review.',lambda r:r['exit']!=0 or bool(r['output']['unresolved_issues']))
trial(sskill,'lp-secondary-base',sec,'Whole-interest price190; half-sale cash90 after allocated fees/carry; retained reference NAV105; no roll.',lambda r:r['exit']==0 and all(Decimal(r['output']['results']['options'][0][k])==Decimal(v) for k,v in [('adjusted_whole_interest_price','190'),('net_cash_at_settlement','90'),('retained_reference_nav','105'),('net_rolled_capital','0')]))
trial(sskill,'gp-continuation-base',gp,'Whole price190, cash66, rolled109, fees6, carry9, future commitment30; no selected option.',lambda r:r['exit']==0 and all(Decimal(r['output']['results']['options'][0][k])==Decimal(v) for k,v in [('net_cash_at_settlement','66'),('net_rolled_capital','109'),('total_transaction_fees','6'),('total_crystallized_carry','9'),('new_uncalled_commitment','30')]) and r['output']['results']['selected_option'] is None)
v=copy.deepcopy(sec);v['interim_flows'][0]['date']='2026-10-05'
trial(sskill,'future-interim-event',v,'Future call cannot be treated as observed interim purchase-price true-up.',lambda r:r['exit']!=0)
v=copy.deepcopy(sec);v['options'][0]['new_uncalled_commitment']='30'
trial(sskill,'lp-ignored-gp-commitment',v,'An LP-sale input carrying an unsupported new continuation commitment must not silently erase it to zero with no issue.',lambda r:r['exit']!=0 or bool(r['output']['unresolved_issues']))
v=copy.deepcopy(gp);v['options'][0].update(status_quo_claimed=True,new_management_fee_rate='0.02',new_carried_interest_rate='0.20',cash_fees='0',cash_crystallized_carry='0',roll_fees='0',roll_crystallized_carry='0',upfront_new_capital='0',new_uncalled_commitment='30')
trial(sskill,'status-quo-new-commitment',v,'Claimed unchanged economics alongside an additional commitment requires explicit review issue.',lambda r:r['exit']!=0 or bool(r['output']['unresolved_issues']))
trial(iskill,'institutional-base',inst,'PV194/down197/up191; duration6/3.88=1.546391752577, convexity0; assets300/gap106; base cash headroom10/20; downside assets250 and cash headroom0/5.',lambda r:r['exit']==0 and r['output_validation_exit']==0 and r['output']['results']['effective_duration']=='1.546391752577' and Decimal(r['output']['results']['effective_convexity'])==0 and [Decimal(x['headroom']) for x in r['output']['results']['scenarios'][0]['cash_coverage']]==[10,20] and [Decimal(x['headroom']) for x in r['output']['results']['scenarios'][1]['cash_coverage']]==[0,5] and Decimal(r['output']['results']['scenarios'][0]['funding_gap'])==106)
v=copy.deepcopy(inst);v['assets'][1]['valuation_date']='2026-09-01'
trial(iskill,'stale-real-asset',v,'Stale real-asset valuation withholds dependent assets/funding/cash coverage, not the independent liability PV.',lambda r:r['exit']==0 and r['output']['results']['scenarios'][0]['asset_value'] is None and r['output']['results']['scenarios'][0]['cash_coverage']==[] and Decimal(r['output']['results']['liability_present_values']['base'])==194)
v=copy.deepcopy(inst);v['asset_cashflows'][1]['amount']='101'
trial(iskill,'repeated-principal',v,'Principal151 against liquidatable asset150 cannot be counted as available cash.',lambda r:r['exit']!=0)
v=copy.deepcopy(inst);v['scenarios'][0]['asset_shocks'][0]['price_return']='-0.5'
trial(iskill,'stressed-principal-exceeds-value',v,'Unreduced principal150 against stressed liquidatable75 withholds dependent asset/cash measures.',lambda r:r['exit']==0 and r['output']['results']['scenarios'][0]['asset_value'] is None and r['output']['results']['scenarios'][0]['cash_coverage']==[])
v=copy.deepcopy(inst);v['discount_factors'][1]['due_date']='2026-12-01'
trial(iskill,'mismatched-liability-factor',v,'A factor for a different liability date cannot be used.',lambda r:r['exit']!=0)
report={'reviewer':'independent sustainability/tokenized/jurisdiction author','basis':'Fresh synthetic raw requests and hand-derived expectations, no target package golden outputs.','checks':len(results),'passed':sum(r['passed'] for r in results),'results':results}
save('report',report)
print(json.dumps({'checks':report['checks'],'passed':report['passed'],'failures':[{'case':r['case'],'issues':r.get('issues'),'stderr':r.get('stderr')} for r in results if not r['passed']]},indent=2))
raise SystemExit(any(not r['passed'] for r in results))
