import json,hashlib,datetime
from pathlib import Path
from decimal import Decimal as D
ROOT=Path('/tmp/insurance-p3-forward-actuarial');REPO=Path('/Users/taylor/DevRepo/Skills/fsi-skills-library')
idx=json.loads((ROOT/'case_index.json').read_text());freeze=json.loads((ROOT/'freeze_manifest.json').read_text());checks=[];current=None

def check(name,actual,expected,kind='business-control'):
 ok=actual==expected;checks.append({'case':current,'name':name,'kind':kind,'actual':actual,'expected':expected,'pass':ok});assert ok,(name,actual,expected)
def num(name,actual,expected,tolerance='1e-20'):
 delta=abs(D(str(actual))-D(str(expected)));ok=delta<=D(tolerance);checks.append({'case':current,'name':name,'kind':'arithmetic','actual':str(actual),'expected':str(expected),'absolute_difference':str(delta),'tolerance':tolerance,'pass':ok});assert ok,(name,actual,expected)
for slug in idx:
 current=slug;base=ROOT/slug;run=base/('mapped_v2' if slug in ['experience','reinsurance','close'] else '');inp=json.loads((run/'native_input.json').read_text());out=json.loads((run/'output.json').read_text());r=out['results'];e=json.loads((base/'independent_expectations.json').read_text())
 check('source_document faithfully retained',out['source_document'],inp,'source-fidelity')
 check('all supplied unresolved issues retained',all(x in out['unresolved_issues'] for x in inp['unresolved_issues']),True,'missingness')
 check('all synthetic evidence dated no later than as_of',all(s['as_of']<=inp['as_of'] for s in inp['sources']),True,'dates')
 check('profile effectiveness covers review date',inp['data']['profile']['effective_from']<=inp['as_of']<=inp['data']['profile']['effective_to'],True,'dates')
 check('source content agrees with frozen raw source sections',{s['source_ref']:s['extraction_text'] for s in inp['sources']},json.loads((base/'raw_sources.json').read_text()),'source-fidelity')
 check('partial status preserves unresolved source review',out['status'],'needs-data','missingness')
 check('partial completeness',out['completeness'],'partial','missingness');check('partial evaluability',out['evaluability'],'partial','missingness')
 check('approval remains absent',out['artifact']['approval'],'not_requested','authority');check('execution remains absent',out['artifact']['execution'],'not_performed','authority');check('evidence not authenticated',out['artifact']['evidence_assurance'],'supplied_not_authenticated','authority')
 check('original raw/native/request/expectations/mapping hashes unchanged',all(hashlib.sha256((ROOT/k).read_bytes()).hexdigest()==h for k,h in freeze['inputs'].items() if k.startswith(slug+'/')),True,'freeze-integrity')
 if slug=='experience':
  for s in r['segments']:
   k=s['segment_id'];days=e['days_by_segment'][k];num(k+' exposure days',s['exposure_days'],days);num(k+' exposure years',s['exposure_years'],D(days)/365);num(k+' event count',s['observed_events'],1);num(k+' expected events',s['expected_events'],D(days)/365*D('.1' if k=='A' else '.2'));num(k+' central rate',s['central_observed_rate'],D(365)/days);num(k+' A/E',s['actual_to_expected'],D(365)/D(days)/D('.1' if k=='A' else '.2'))
  for x in r['risk_sets']:num(x['event_date']+' risk count',x['at_risk_before_event'],e['risk_sets'][x['event_date']])
  for x,days in zip(r['rows'],[31,167,90,61]):num(x['record_id']+' elapsed days',x['exposure_days'],days)
  num('total exposure',sum(D(x['exposure_years']) for x in r['segments']),e['total_exposure']);num('total expected deaths',sum(D(x['expected_events']) for x in r['segments']),e['expected_events']);num('total A/E',D(2)/sum(D(x['expected_events']) for x in r['segments']),e['actual_expected'])
  check('no credibility claim',r['credibility_assessed'],False,'authority')
 elif slug=='pricing':
  for i,row in enumerate(r['projection']):
   for k,ek in [('opening_policies','opening'),('expected_deaths','deaths'),('expected_lapses','lapses'),('closing_policies','closing')]:num(f'year{i+1} {k}',row[k],e[ek][i])
   num(f'year{i+1} total benefit',D(row['eoy_benefits'])+D(row['eoy_terminal_benefit']),e['benefits_eoy'][i])
  num('terminal paid once',r['projection'][1]['eoy_terminal_benefit'],e['terminal'])
  for k,ek in [('pv_premiums','pv_premiums'),('pv_expenses','pv_expenses'),('pv_benefits','pv_benefits'),('pv_net_cashflow','net'),('net_cashflow_margin','margin')]:num(k,r[k],e[ek])
  check('price not approved',r['price_approved'],False,'authority');check('capital/tax/reserves not modeled',r['capital_tax_and_reserves_modeled'],False,'method-scope')
 elif slug=='valuation':
  for row in r['cashflows']:num(row['cashflow_id']+' PV',row['present_value'],e['row_pv'][row['cashflow_id']])
  for name,a,b in [('PV',r['cashflow_pv'],e['pv']),('reported PV residual',r['pv_reconciliation']['difference'],e['pv_vs_reported']),('book bridge',r['book_bridge']['expected_book'],e['adjusted_pv']),('book residual',r['book_bridge']['difference'],e['book_residual']),('rollforward',r['rollforward']['expected_closing'],e['rollforward']),('rollforward residual',r['rollforward']['difference'],e['rollforward_residual'])]:num(name,a,b)
  check('both ten-dollar breaks flagged',set(x['code'] for x in out['findings']),{'cashflow_pv_break','pv_to_book_break'},'business-control');check('no reserve-method validation claim',r['reserve_method_validated'],False,'method-scope')
 elif slug=='alm':
  for s in r['scenarios']:
   ex=e[s['scenario_id']]
   for k,ek in [('asset_cashflow_pv','asset_pv'),('liability_cashflow_pv','liability_pv'),('pv_surplus','surplus'),('funding_gap','funding_gap'),('asset_pv_weighted_time','asset_weighted_maturity'),('liability_pv_weighted_time','liability_weighted_maturity')]:num(s['scenario_id']+' '+k,s[k],ex[ek],'1e-10')
   for i,x in enumerate(s['liquidity_ladder']):num(s['scenario_id']+' cash '+str(i),x['cumulative_cash'],ex['cash_balances'][i])
  num('surplus change',r['scenarios'][1]['surplus_change_from_base'],e['change'],'1e-10');check('no adequacy opinion',r['asset_adequacy_opinion'],False,'authority');check('no dynamic option response',r['reinvestment_or_option_response_modeled'],False,'method-scope')
 elif slug=='reinsurance':
  for k,ek in [('signed_premium','signed_premium'),('expected_signed_loss','expected_signed_loss'),('expected_net_underwriting_cashflow','expected_net'),('probability_negative_underwriting_cashflow','negative_probability'),('expected_loss_ratio','expected_loss_ratio')]:num(k,r[k],e[ek])
  num('total signed expenses',r['signed_expenses'],e['variable_expenses']+e['fixed_expenses'])
  for s in r['scenarios']:num(s['scenario_id']+' loss',s['signed_loss'],e['quiet_loss' if s['scenario_id']=='quiet' else 'active_signed_loss']);num(s['scenario_id']+' net',s['net_underwriting_cashflow'],e[s['scenario_id']+'_net'])
  ev={x['event_id']:x for x in r['scenarios'][1]['events']}
  for k,before,after in [('A',200,200),('B',200,100),('C',0,0),('D',0,0)]:num(k+' occurrence loss',ev[k]['occurrence_layer_loss'],before);num(k+' post aggregate loss',ev[k]['after_annual_aggregate'],after)
  check('boundary event excluded',bool(ev['C']['coverage_exceptions']),True);check('uncovered peril excluded',bool(ev['D']['coverage_exceptions']),True);check('aggregate exhausted',r['scenarios'][1]['aggregate_exhausted'],True);check('no binding authority',r['bind_authority_granted'],False,'authority');check('no risk transfer conclusion',r['risk_transfer_or_price_adequacy_determined'],False,'authority')
 elif slug=='close':
  for row in r['account_reconciliations']:
   for k,ek in [('difference_before','before'),('proposed_gl_delta','delta'),('pro_forma_gl_balance','proforma_gl'),('difference_after_proposal','after')]:num(row['account_id']+' '+k,row[k],e[row['account_id']][ek])
  num('balanced proposed journal',r['journal_checks'][0]['signed_sum'],0);check('journal stays unposted',r['journal_checks'][0]['posted'],False,'authority');check('no posting authority',r['journal_posting_authorized'],False,'authority');check('close not certified',r['close_certified'],False,'authority')
 elif slug=='capital':
  for k,ek in [('available_capital','available'),('available_control_difference','base_control_difference'),('ratio_pct','ratio_pct')]:num(k,r[k],e[ek])
  s=r['stress_bridges'][0]
  for k,ek in [('available_capital','stress_available'),('required_capital','stress_requirement'),('available_control_difference','stress_available_control_difference'),('requirement_control_difference','stress_requirement_control_difference'),('ratio_pct','stress_ratio_pct')]:num('stress '+k,s[k],e[ek])
  check('denominator name preserved',r['denominator_name'],'Internal economic requirement','method-scope');check('base threshold comparisons',{x['threshold_id']:x['comparison'] for x in r['threshold_comparisons']},e['base_thresholds']);check('stress threshold comparisons',{x['threshold_id']:x['comparison'] for x in s['threshold_comparisons']},e['stress_thresholds']);check('no regulatory action',r['regulatory_action_determined'],False,'authority');check('no solvency certification',r['solvency_certified'],False,'authority')
 (base/'independent_check.json').write_text(json.dumps([c for c in checks if c['case']==slug],indent=2,default=lambda x:sorted(x) if isinstance(x,set) else str(x))+'\n')

counts={slug:{'arithmetic':sum(x['case']==slug and x['kind']=='arithmetic' for x in checks),'other':sum(x['case']==slug and x['kind']!='arithmetic' for x in checks)} for slug in idx}
(ROOT/'independent_check_summary.json').write_text(json.dumps({'counts':counts,'arithmetic_total':sum(x['kind']=='arithmetic' for x in checks),'other_total':sum(x['kind']!='arithmetic' for x in checks),'all_pass':all(x['pass'] for x in checks)},indent=2)+'\n')
# Freeze current hashes without copying packages; initial hashes remain in freeze_manifest.json.
current_hashes={skill:{path:hashlib.sha256((REPO/path).read_bytes()).hexdigest() for path in hashes} for skill,hashes in freeze['packages'].items()}
(ROOT/'post_review_package_hashes.json').write_text(json.dumps({'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),'hashes':current_hashes,'changes_since_initial_freeze':[p for s,h in freeze['packages'].items() for p,sha in h.items() if current_hashes[s][p]!=sha]},indent=2)+'\n')
print(json.dumps({'checks':counts,'total_arithmetic':sum(x['kind']=='arithmetic' for x in checks),'total_other':sum(x['kind']!='arithmetic' for x in checks),'all_pass':True},indent=2))
