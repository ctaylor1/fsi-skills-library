import json,pathlib,math,subprocess,os,hashlib,datetime
from fractions import Fraction
D=pathlib.Path('/private/tmp/ir-remaining-findings-independent');P='/Users/taylor/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3';R=pathlib.Path('/Users/taylor/DevRepo/Skills/fsi-skills-library/skills/investment-research')
checks=[]
def check(case,label,actual,expected,approx=False):
 ok=math.isclose(actual,float(expected),rel_tol=1e-14,abs_tol=1e-14) if approx and actual is not None else actual==expected
 checks.append({'case':case,'assertion':label,'expected':str(expected) if isinstance(expected,Fraction) else expected,'actual':actual,'pass':ok})
def read(case):return json.loads((D/case/'output.json').read_text())
for case in ['issuer_base','issuer_ocf_omitted','issuer_capex_zero','issuer_ffo_unknown','issuer_debt_reconciliation_omitted']:
 o=read(case);r=o['results'];m=r['credit_metrics'];missing_debt='debt_reconciliation_omitted' in case
 for basis in ['reported_ebitda','analyst_adjusted_ebitda']:
  check(case,basis+'.ebitda',m[basis]['ebitda'],96);check(case,basis+'.interest_coverage_x',m[basis]['interest_coverage_x'],8);check(case,basis+'.gross_leverage_x',m[basis]['gross_leverage_x'],None if missing_debt else 3.75);check(case,basis+'.net_leverage_x',m[basis]['net_leverage_x'],None if missing_debt else 3.5)
 fcf=None if case=='issuer_ocf_omitted' else 54 if case=='issuer_capex_zero' else 36
 check(case,'free_cash_flow',r['cash_flow']['free_cash_flow'],fcf)
 expected_ffo=None if missing_debt or case=='issuer_ffo_unknown' else Fraction(7,60)
 check(case,'ffo_to_debt',r['cash_flow']['ffo_to_debt'],expected_ffo,approx=expected_ffo is not None)
 check(case,'adjustment total',r['evidence_reconciliation']['ebitda_adjustments']['signed_adjustment_total'],0)
 check(case,'no approval or action',o['authority_granted'] is False and o['action_taken'] is False and o['professional_acceptance']=='not-established' and o['source_truth']=='unverified',True)
 check(case,'status accounts for unknown legal priority',o['status'],'partial')
 check(case,'retained original byte-equal', (D/case/'original.json').read_bytes()==(D/case/'request.json').read_bytes(),True)
 if case=='issuer_base':
  for key,exp in [('included_principal_total',366),('carrying_value_bridge_total',-6),('reconstructed_gross_debt',360)]:check(case,key,r['evidence_reconciliation']['debt_inventory'][key],exp)
 if case=='issuer_ocf_omitted':check(case,'field-named OCF issue',any('financials.operating_cash_flow: missing evidence' in i for i in o['unresolved_issues']),True)
 if case=='issuer_capex_zero':check(case,'zero capex not missing',any('capex' in i for i in o['unresolved_issues']),False)
 if case=='issuer_ffo_unknown':check(case,'field-named FFO issue',any('financials.funds_from_operations: missing evidence' in i for i in o['unresolved_issues']),True)
 if missing_debt:check(case,'no bridge lineage',o['calculation_lineage'][0]['bridge_ids'],[])
for case in ['surveillance_comparable','surveillance_comparable_current_evidence_omitted']:
 o=read(case);r=o['results'];missing='omitted' in case
 values={'prior':{'gross_leverage_x':Fraction(11,3),'net_leverage_x':Fraction(154,45),'interest_coverage_x':Fraction(90,11),'fixed_charge_proxy_x':Fraction(74,11)},'current':{'gross_leverage_x':Fraction(15,4),'net_leverage_x':Fraction(7,2),'interest_coverage_x':Fraction(8),'fixed_charge_proxy_x':Fraction(13,2)}}
 for period,metrics in values.items():
  for k,v in metrics.items():check(case,period+'.'+k,r['period_metrics'][period][k],v,approx=True)
  check(case,period+' incomplete maturity inventory withholds liquidity',r['period_metrics'][period]['liquidity_to_known_maturity_x'],None)
 for k in values['prior']:check(case,'metric change '+k,r['metric_changes'][k],values['current'][k]-values['prior'][k],approx=True)
 check(case,'spread delta',r['spread_change_bps'],None if missing else 44.75)
 check(case,'spread reconciliation',r['spread_reconciliation']['status'],'withheld' if missing else 'reconciled-supplied-evidence')
 check(case,'alerts',r['alerts'],[] if missing else ['spread widened beyond supplied threshold'])
 if missing:
  check(case,'withheld spread observations empty',r['spread_reconciliation']['observations'],[]);check(case,'withheld mapping empty',r['spread_reconciliation']['instrument_mapping'],None);check(case,'current financial metrics retained',r['period_metrics'],read('surveillance_comparable')['results']['period_metrics'])
 check(case,'status accounts for maturity incompleteness',o['status'],'partial')
 check(case,'no authority or action',o['authority_granted'] is False and o['action_taken'] is False and r['position_action']=='none' and r['thesis_action']=='unchanged' and o['source_truth']=='unverified',True)
 check(case,'retained original byte-equal',(D/case/'original.json').read_bytes()==(D/case/'request.json').read_bytes(),True)
for case in ['surveillance_base','surveillance_current_evidence_omitted']:
 text=(D/case/'input.stdout').read_text()+(D/case/'input.stderr').read_text()+(D/case/'calculate.stderr').read_text();check(case,'controlled period mismatch', 'period duration differs; no annual/interim mixing' in text and 'Traceback' not in text,True);check(case,'no output emitted',(D/case/'output.json').exists(),False)
legacy=D/'surveillance_legacy_received';args=[P,'-B',str(R/'issuer-credit-surveillance-reviewer/scripts/validate_output.py'),str(legacy/'request.json'),'--input',str(legacy/'original.json')];p=subprocess.run(args,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True);(legacy/'output-check.stdout').write_text(p.stdout);(legacy/'output-check.stderr').write_text(p.stderr);(legacy/'output-check-command.json').write_text(json.dumps({'argv':args,'exit_code':p.returncode,'note':'No computed output exists. Received legacy intake intentionally presented to output entrypoint only to confirm controlled legacy migration rejection.'},indent=2)+'\n')
for prefix in ['input','calculate','output-check']:
 text=(legacy/(prefix+'.stdout')).read_text()+(legacy/(prefix+'.stderr')).read_text();check('surveillance_legacy_received',prefix+' rejects with controlled migration error','legacy surveillance migration required' in text and 'Traceback' not in text,True)
check('packages','hashes unchanged',json.loads((D/'package-hashes-before.json').read_text()),json.loads((D/'package-hashes-after.json').read_text()))
for checkrow in checks:
 if checkrow['case']=='packages':checkrow['actual']='64-file hash manifest';checkrow['expected']='Identical 64-file hash manifest'
summary={'assertions':len(checks),'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'comparison_note':'Financial ratios checked independently against rational arithmetic using 1e-14 tolerance only for JSON float display; exact finite spread44.75 and structural controls checked by exact equality. No tolerance changes native reconciliation.','checks':checks}
(D/'independent-assertion-outcomes.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items() if k!='checks'},indent=2))
