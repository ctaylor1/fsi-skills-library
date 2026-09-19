import json,pathlib
from decimal import Decimal as D
from datetime import date
R=pathlib.Path('/tmp/insurance-p2-forward-operations');checks=[]
def get(k):return json.loads((R/k/'native-output.json').read_text())
def check(case,name,expected,actual):
    same=expected==actual
    if isinstance(expected,str) and isinstance(actual,str):
        try: same=D(expected)==D(actual)
        except: pass
    checks.append(dict(case=case,check=name,expected=expected,actual=actual,pass_=same))
b=get('billing')['results']
# Independent reconstruction from raw LEDGER, not native movement_register or domain methods.
movement=D('600')-D('700')-D('100')-D('200')+D('200')-D('650')
close=D('1000')+movement
check('billing','account movement',str(movement),str(D(b['movement_total'])))
check('billing','calculated close',str(close),str(D(b['calculated_closing_balance'])))
check('billing','calculated minus reported',str(close-D('420')),str(D(b['difference'])))
check('billing','old invoice balance',str(D('1000')-D('700')-D('100')),str(D(b['invoice_aging'][0]['outstanding'])))
check('billing','old invoice days past due',(date(2026,8,31)-date(2026,7,15)).days,b['invoice_aging'][0]['days_past_due'])
check('billing','unapplied live receipt',str(D('650')-D('600')),str(D(b['unapplied_cash_credits']['R-3'])))
check('billing','invoice less unapplied equals account balance',str(D(b['invoice_aging'][0]['outstanding'])-D(b['unapplied_cash_credits']['R-3'])),str(D(b['calculated_closing_balance'])))
p=get('policy')['results'];check('policy','change table before uses actual current policy value','12 Main St',p['proposed_changes'][0]['before'])
check('policy','stale before is flagged',True,any(f['code']=='before-value-conflict' for f in get('policy')['findings']))
m=get('placement')['results']['market_assessments'];check('placement','South total',str(D('10900')+D('200')+D('545')),str(D(m[1]['quoted_total'])))
check('placement','North total withheld for pending taxes',None,m[0]['quoted_total']);check('placement','unsupported satisfied subjectivity unresolved','unknown',m[0]['subjectivities'][0]['observed_status'])
a=get('delegation')['results'];check('delegation','aggregate remaining',str(D('2000000')-D('1880000')),str(D(a['aggregate_remaining_before_request'])))
check('delegation','projected usage',str(D('1880000')+D('180000')),str(D(a['projected_aggregate_used'])))
check('delegation','signed within-report premium difference',str(D('94750.50')-D('95000.00')),a['bordereaux_checks'][0]['reported_minus_expected'])
check('delegation','late report flag',True,a['bordereaux_checks'][0]['late_or_overdue'])
check('producer','conflicting individual license unresolved','unknown',get('producer')['results']['scope_checks'][0]['checks'][0]['status'])
check('producer','absent agency appointment unresolved','unknown',get('producer')['results']['scope_checks'][1]['checks'][1]['status'])
life=get('life')['results'];check('life','contradictory liquidity remains unresolved','missing-or-unresolved',next(x for x in life['consumer_matrix'] if x['topic']=='liquidity-needs')['status'])
check('life','no suitability decision','not-made',life['suitability_or_best_interest_decision'])
for k in json.loads((R/'cases.json').read_text()):
 out=get(k);check(k,'approval remains unrequested','not_requested',out['approval']);check(k,'execution remains unperformed','not_performed',out['execution'])
(R/'independent-checks.json').write_text(json.dumps(checks,indent=2)+'\n')
(R/'independent-arithmetic.md').write_text('''# Independent arithmetic from raw sources

All amounts are synthetic, in USD. Computed using Decimal without package imports.

- Billing: 1000 + 600 - 700 - 100 - 200 + 200 - 650 = 150. Reported close 420; calculated minus reported = -270.
- Opening invoice OLD-1: 1000 - 700 - 100 = 200; 47 days past due at 2026-08-31. NEW-1: 600 - 600 = 0. R-3 unapplied = 650 - 600 = 50. Net invoice balance 200 less unapplied 50 = account receivable 150.
- Placement South: 10900 + 200 + 545 = 11645. North current version cannot total because tax is unknown. The superseded North total would be 12850 but is not the selected current response.
- Delegation per-risk headroom: 250000 - 180000 = 70000. Aggregate remaining before request: 2000000 - 1880000 = 120000. Projected usage 1880000 + 180000 = 2060000, exceeding aggregate by 60000. Reporting discrepancy: 94750.50 - 95000.00 = -249.50; received 2026-09-16 versus due 2026-09-10 = six calendar days late. The package incorrectly withholds the within-report monetary difference because authority and report use different amount bases.
- Life replacement illustration: 103000 account value - 3000 stated surrender charge = 100000 before any unprovided tax or other adjustments; equals stated new premium. Stated commission 5% × 100000 = 5000. This arithmetic does not establish net tax proceeds, comparative value, suitability or sale approval.
''')
print(json.dumps({'checks':len(checks),'passed':sum(x['pass_'] for x in checks),'failures':[x for x in checks if not x['pass_']]},indent=2))
