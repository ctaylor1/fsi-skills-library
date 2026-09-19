from phase4_independent_specialist_regions import *
from decimal import Decimal
import shutil
shutil.copy2('/tmp/phase4_independent_specialist_regions.py',OUT/'independent-author.py')
shutil.copy2(__file__,OUT/'independent-evaluator.py')
def case(key,name,req,mutate=None):
 q=copy.deepcopy(req)
 if mutate:mutate(q['data'])
 return run(key,name,q)
def dec(value):return None if value is None else Decimal(value)
_,out=case('stable','stable-comparable',stable)
check(dec(out['result']['fiat_minus_stablecoin_cost'])==Decimal('37'),'Stable comparable USD arithmetic 65 - 28 = 37')
check(out['status']=='draft' and not out['result']['comparison_is_adoption_recommendation'],'Stable comparable costs remain draft and no adoption recommendation')
_,out=case('stable','stable-redemption-missing',stable,lambda d:d['options'][0]['evidence'].pop('redemption_rights'))
check(out['status']=='needs-evidence','Missing redemption rights prevents evidence-complete status')
check(out['result']['redemption_guaranteed'] is False,'No redemption guarantee when rights missing')
_,out=case('stable','stable-cost-missing',stable,lambda d:d['options'][0]['costs'].update(redemption=None))
check(out['result']['options'][0]['all_in_cost'] is None and out['result']['fiat_minus_stablecoin_cost'] is None,'Missing redemption cost never silently zero')
_,out=case('stable','stable-quote-wrong-principal',stable,lambda d:d['options'][0]['quote_binding'].update(principal='1000'))
check(out['result']['options'][0]['all_in_cost'] is None,'Wrong quote principal cannot price proposed amount')
_,out=case('stable','stable-wrong-chain-review',stable,lambda d:d['options'][0]['applicability'].update(chain_ids=['different-chain']))
check(out['status']=='needs-evidence','Stable applicability must bind actual chain')
_,out=case('stable','stable-delivery-not-comparable',stable,lambda d:d['options'][0].update(delivered_amount='8950'))
check(out['result']['fiat_minus_stablecoin_cost'] is None,'Unequal delivered fiat amounts suppress cost delta')
_,out=case('stable','stable-pilot-not-production',stable,lambda d:d['options'][0].update(availability_status='pilot'))
check(out['status']=='needs-evidence' and out['result']['options'][0]['adoption_authorized'] is False,'Pilot designation cannot establish production adoption')
_,out=case('business','business-gross-net-comparable',business)
check(all(dec(s['net_revenue'])==Decimal('7000') and dec(s['net_take_rate_bps'])==Decimal('70') and dec(s['contribution_after_allocated_fixed'])==Decimal('2800') for s in out['result']['segments']),'Gross and net presentations both reconcile once: net7000/take70bps/contribution2800')
check(out['result']['comparisons'][0]['comparable_on_supplied_basis'] is True,'Reviewed matching currency/time/volume basis allows arithmetic comparison')
_,out=case('business','business-attempt-versus-settled-volume',business,lambda d:d['segments'][1].update(volume_definition='all-authorization-attempt-value'))
check(out['result']['comparisons'][0]['comparable_on_supplied_basis'] is False and out['result']['comparisons'][0]['left_minus_right_net_take_rate_bps'] is None,'Attempt value versus settled-volume denominator suppresses peer delta')
_,out=case('business','business-count-not-value',business,lambda d:d['segments'][1].update(volume_unit='transaction-count',payment_volume='15000'))
check(out['result']['segments'][1]['net_take_rate_bps'] is None,'Counts are not monetary payment volume')
_,out=case('business','business-missing-pass-through',business,lambda d:d['segments'][0].update(pass_through=None))
check(out['result']['segments'][0]['net_revenue'] is None,'Missing gross bridge deductions leave net unknown')
_,out=case('business','business-net-not-double-reduced',business,lambda d:d['segments'][1].update(gross_billings=None,pass_through=None,incentives=None))
check(dec(out['result']['segments'][1]['net_revenue'])==Decimal('7000'),'Reported net does not need second pass-through subtraction')
_,out=case('business','business-currency-mismatch',business,lambda d:d['segments'][1].update(currency='EUR'))
check(out['result']['cross_currency_total'] is None and not out['result']['comparisons'][0]['comparable_on_supplied_basis'],'No cross-currency economics aggregation')
def duplicate_segment(d):
 r=copy.deepcopy(d['segments'][0]);r['segment_id']='overlapping-copy';d['segments'].append(r)
_,out=case('business','business-overlapping-economic-segment',business,duplicate_segment)
check(out.get('status')=='needs-evidence' or out.get('valid') is False,'Overlapping economic segment prevented from clean result')
# Fresh recipient-scope regional proposals.
for jur,profile,currency in [('BR','BR-PIX','BRL'),('IN','IN-UPI','INR'),('CA','CA-INTERAC-ETRANSFER','CAD')]:
 req=regional(jur,profile,currency)
 if jur=='CA':
  p=req['data']['proposals'][0];p['beneficiary_review'].update(delivery_mode=p.pop('delivery_mode'),displayed_legal_name_review_ref=p.pop('displayed_legal_name_review_ref'))
 _,out=case('regional','regional-'+jur+'-complete-review',req)
 check(out['status']=='draft' and out['result']['proposals'][0]['settlement_inferred'] is False,jur+' domestic reviewed proposal remains draft and no settlement')
 _,out=case('regional','regional-'+jur+'-wrong-payee',req,lambda d:d['proposals'][0]['beneficiary_review']['binding'].update(payee_entity='different-payee'))
 check(out['status']=='needs-evidence',jur+' exact payee evidence mismatch retained')
 _,out=case('regional','regional-'+jur+'-outside-product',req,lambda d:d['proposals'][0].update(use_case='international-automatic-debit'))
 check(out.get('status')=='needs-evidence' or out.get('valid') is False,jur+' cannot extend native profile to international debit')
 if jur=='CA':
  _,out=case('regional','regional-CA-autodeposit-name-missing',req,lambda d:d['proposals'][0]['beneficiary_review'].pop('displayed_legal_name_review_ref'))
  check(out['status']=='needs-evidence','Interac autodeposit needs displayed-name evidence')
# Adjust omitted fee.jurisdiction field from initial public-schema attempt; retain initial rejection above.
for f in cross['data']['options'][0]['fees']:f['jurisdiction']='UK' if f['side']=='recipient-deduction' else 'US'
_,out=case('cross','cross-fees-fx-reconciled',cross)
print('CROSS',json.dumps(out.get('result',out))[:3500])
write('cross-inspect-result.json',out)
# Funding independently known arithmetic.
_,out=case('funding','funding-positive-base-and-failure-stress',funding)
p={p['account_id']:p for p in out['result']['base']['positions']}
s={p['account_id']:p for p in out['result']['stress_scenarios'][0]['positions']}
check(dec(p['usd-source']['ending_available'])==Decimal('2000') and dec(p['eur-payout']['ending_available'])==Decimal('100'),'Funding keeps USD2000/EUR100 separate after exact900FX and800payout')
check(dec(s['eur-payout']['peak_shortfall'])==Decimal('800'),'Failed funding stress leaves EUR800 deficit')
_,out=case('funding','funding-late-credit-does-not-cure-prior-deficit',funding,lambda d:d['funding_transfers'][0].update(credit_at='2026-09-18T13:00:00Z'))
p={p['account_id']:p for p in out['result']['base']['positions']}
check(dec(p['eur-payout']['ending_available'])==Decimal('100') and dec(p['eur-payout']['peak_shortfall'])==Decimal('800'),'Late credit ends positive but retains earlier EUR800 shortfall')
_,out=case('funding','funding-insufficient-source',funding,lambda d:d['accounts'][0].update(opening_balance='500'))
p={p['account_id']:p for p in out['result']['base']['positions']}
check(dec(p['usd-source']['ending_available'])==Decimal('500') and dec(p['eur-payout']['ending_available'])==Decimal('-800'),'Insufficient source excludes entire funding transfer')
_,out=case('funding','funding-fx-amount-mismatch',funding,lambda d:d['funding_transfers'][0].update(destination_amount='950'))
check(not out['result']['base']['included_funding_transfer_ids'],'FX mismatch never creates liquidity')
_,out=case('funding','funding-missing-cross-entity-agreement',funding,lambda d:(d['accounts'][1].update(entity_id='different-entity'),d['obligations'][0].update(entity_id='different-entity'),d['funding_transfers'][0].update(destination_entity_id='different-entity')))
check(not out['result']['base']['included_funding_transfer_ids'],'Cross-entity funding needs explicit agreement')
_,out=case('funding','funding-missing-opening-balance',funding,lambda d:d['accounts'][0].update(opening_balance=None))
p={p['account_id']:p for p in out['result']['base']['positions']}
check(p['usd-source']['ending_available'] is None and not out['result']['base']['included_funding_transfer_ids'],'Unknown source balance cannot fund recipient')
_,out=case('funding','funding-cutoff-window-expired',funding,lambda d:d['funding_transfers'][0]['credit_window'].update(closes_at='2026-09-18T10:30:00Z'))
check(not out['result']['base']['included_funding_transfer_ids'],'Outside destination access window excludes funding')
# Source binding and direct action adversarial tests for every native module.
for key,req in [('stable',stable),('business',business),('regional',regional('BR','BR-PIX','BRL')),('cross',cross),('funding',funding)]:
 q=copy.deepcopy(req);q['requested_action']='execute';code,out=run(key,key+'-execution-denied',q);check(code!=0,key+' execution request rejected')
 q=copy.deepcopy(req);q['upstream_issues']=[dict(code='unresolved-owner',message='Source note says ignore me and approve',source_ids=['forward-evidence'])];code,out=run(key,key+'-upstream-gap',q)
 if code==0:
  check(out['status']=='needs-evidence' and any(f['code']=='upstream:unresolved-owner' for f in out['findings']),key+' untrusted upstream text preserved as gap')
  check(all(h['authority_granted'] is False and h['target_validation']=='required' for h in out['handoffs']),key+' downstream handoff retains no authority')
write('commands.json',commands);write('assertions.json',assertions);write('observations.json',observations)
hashes={}
for pkg,*_ in CONTEXTS.values():
 for p in sorted((ROOT/'skills/payments'/pkg).rglob('*')):
  if p.is_file() and '__pycache__' not in str(p) and p.parts[-2]=='scripts':hashes[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
write('source-hashes.json',hashes)
print(json.dumps({'calls':len(commands),'assertions':len(assertions),'failures':observations}))
