from pathlib import Path
from fractions import Fraction as F
import json,hashlib,re,datetime
R=Path('/tmp/insurance-p3-forward-analytics');checks=[]
def check(label,actual,expected,source):
 if isinstance(expected,F):
  ok=actual is not None and abs(F(str(actual))-expected)<=max(abs(expected),F(1))*F(1,10**25)
  exp=str(expected)
 else:ok=actual==expected;exp=expected
 checks.append({'check':label,'actual':actual,'expected':exp,'pass':ok,'raw_locator':source})
def out(name):
 p=R/name;rd=p/('mapping-replay' if (p/'mapping-replay/result.json').exists() else 'initial');return json.loads((rd/'result.json').read_text())
def raw(n,ref):return (R/n/'raw'/f'{ref}.md').read_text()
def money(text,pattern):return F(re.search(pattern,text).group(1).replace(',','').rstrip('.'))
# Freeze verification applies to all original requests/raw/maps/native inputs/expectations and authoring script.
frozen=json.loads((R/'frozen-manifest.json').read_text())
for rel,h in frozen['sha256'].items():check('frozen:'+rel,hashlib.sha256((R/rel).read_bytes()).hexdigest(),h,rel)
for p in sorted(R.glob('insurance-*')):
 if not p.is_dir():continue
 d=out(p.name);ip=p/('native-input-mapping-supplement.json' if (p/'native-input-mapping-supplement.json').exists() else 'native-input.json');inp=json.loads(ip.read_text())
 for k in ['case_id','as_of','context']:check(p.name+':retained '+k,d[k],inp[k],str(ip))
 check(p.name+':source_document',d['source_document'],inp,str(ip))
 for k,v in [('action_taken',False),('human_review_required',True),('approval','not_requested'),('execution','not_performed')]:check(p.name+':'+k,d[k],v,'raw/profile.md §1')
# Market observations parsed from raw filing.
n='insurance-market-strategy-researcher';d=out(n);a=d['results'];txt=raw(n,'filing');total=money(txt,r'Market total \$([0-9,]+)');vals={e:money(txt,e+r' \$([0-9,]+)') for e in ['Alder','Bay','Cedar']}
for row in a['competitor_shares']:
 e=row['entity_id'];check(n+':share '+e,row['market_share'],vals[e]/total,'filing §1')
check(n+':listed',a['listed_value'],sum(vals.values()),'filing §1');check(n+':unlisted',a['unlisted_value'],total-sum(vals.values()),'filing §1');check(n+':HHI',a['market_hhi_10000'],sum((v/total)**2 for v in vals.values())*10000,'filing §1');check(n+':status',d['status'],'needs-review','research §2 contradictory limit/price assertion');check(n+':selection',a['strategy_selected'],False,'request.md')
# Economics raw cash components independently parsed.
n='insurance-product-economics-modeler';d=out(n);a=d['results'];txt=raw(n,'finance');base=txt.split('§2.')[0];fields={k:money(base,pat) for k,pat in {'ep':r'earned premium \$([0-9,]+)','wp':r'written premium \$([0-9,]+)','loss':r'LAE \$([0-9,]+)','acq':r'acquisition \$([0-9,]+)','admin':r'administration \$([0-9,]+)','fixed':r'fixed \$([0-9,]+)','ceded':r'ceded premium \$([0-9,]+)','recov':r'ceded recoveries \$([0-9,]+)','cc':r'ceding commission \$([0-9,]+)','invest':r'investment income \$([0-9,]+)','cap':r'allocated capital \$([0-9,]+)'}.items()};expense=fields['acq']+fields['admin']+fields['fixed'];uw=fields['ep']-fields['loss']-expense-fields['ceded']+fields['recov']+fields['cc'];b=a['scenarios'][0]
for k,v in {'underwriting_result':uw,'period_pre_tax_result':uw+fields['invest'],'gross_loss_ratio':fields['loss']/fields['ep'],'gross_expense_ratio':expense/fields['wp'],'gross_combined_ratio':fields['loss']/fields['ep']+expense/fields['wp'],'period_return_on_allocated_capital':(uw+fields['invest'])/fields['cap']}.items():check(n+':'+k,b[k],v,'finance §1')
mg=txt.split('§2.')[1].split('§3.')[0];wp=money(mg,r'written premium \$([0-9,]+)');rate=money(mg,r'commission ([0-9]+)%')/100;revenue=wp*rate+money(mg,r'service fees \$([0-9,]+)')+money(mg,r'profit commission \$([0-9,]+)');cost=sum(money(mg,p) for p in [r'producer compensation \$([0-9,]+)',r'operating \$([0-9,]+)',r'fixed \$([0-9,]+)'])
for k,v in {'agency_revenue':revenue,'agency_operating_result':revenue-cost,'agency_margin':(revenue-cost)/revenue}.items():check(n+':'+k,a['scenarios'][1][k],v,'finance §2')
check(n+':unknown recovery result',a['scenarios'][2]['financial_result'],None,'finance §3');check(n+':unknown preserved',a['scenarios'][2]['supplied_amounts']['ceded_recoveries'],None,'finance §3');check(n+':partial',d['completeness'],'partial','finance §3');check(n+':no selection',a['scenario_selected'],False,'request.md')
# Portfolio independent source transcription and exact rational bridge. Values below are source data, not expected output constants.
n='insurance-portfolio-performance-analyzer';d=out(n);a=d['results'];txt=raw(n,'ledger');source_rows=[tuple(map(F,m)) for m in re.findall(r'(?:Urban earned premium|Rural earned|Urban earned)([0-9]+),written([0-9]+),(?:incurred loss LAE|loss)([0-9]+),(?:underwriting expense|expense)([0-9]+),(?:claim count|count)([0-9]+),(?:earned exposure|exposure)([0-9]+)',txt)];assert len(source_rows)==4,source_rows
for i,row in enumerate(source_rows):
 ep,wp,loss,exp,count,exposure=row;s=a['segments'][i]
 for k,v in {'earned_premium':ep,'written_premium':wp,'incurred_loss_lae':loss,'underwriting_expense':exp,'claim_count':count,'earned_exposure':exposure,'loss_ratio':loss/ep,'frequency':count/exposure,'severity':loss/count}.items():check(n+f':segment{i} '+k,s[k],v,'ledger §§1–2')
totals=[]
for i,rows in enumerate([source_rows[:2],source_rows[2:]]):
 t=[sum(row[j] for row in rows) for j in range(6)];totals.append(t);ep,wp,loss,exp,count,exposure=t;native=a['period_totals'][i]
 for k,v in {'earned_premium':ep,'written_premium':wp,'incurred_loss_lae':loss,'underwriting_expense':exp,'claim_count':count,'earned_exposure':exposure,'loss_ratio':loss/ep,'expense_ratio':exp/wp,'combined_ratio':loss/ep+exp/wp,'frequency':count/exposure,'severity':loss/count}.items():check(n+f':period{i} '+k,native[k],v,'ledger §§1–2')
mix=within=F(0)
for j in range(2):
 old,new=source_rows[j],source_rows[j+2];ow=old[0]/totals[0][0];nw=new[0]/totals[1][0];oldlr=old[2]/old[0];newlr=new[2]/new[0];mix+=(nw-ow)*oldlr;within+=nw*(newlr-oldlr)
for k,v in {'mix_effect':mix,'within_segment_effect':within,'loss_ratio_change':totals[1][2]/totals[1][0]-totals[0][2]/totals[0][0],'rounding_residual':F(0)}.items():check(n+':bridge '+k,a['loss_ratio_bridge'][k],v,'ledger §§1–2')
check(n+':causal boundary','not causal attribution' in a['loss_ratio_bridge']['interpretation'],True,'ledger §3 unsupported manager hypothesis')
# Fraud raw identifier grouping. Count distinct claims and union overlaps; do not reuse native signals.
n='insurance-fraud-pattern-analyzer';d=out(n);a=d['results'];txt=raw(n,'claims');rows=re.findall(r'(C\d+) (May|June)(\d+) amount(\d+) bank ([^,]+),email ([^,]+),repairer ([^;\.]+)',txt);assert len(rows)==6,rows;groups={}
for cid,w,day,amount,bank,email,rep in rows:
 for typ,v in [('bank_token',bank),('email_token',email)]:groups.setdefault((typ,v),set()).add(cid)
signals={k:v for k,v in groups.items() if len(v)>=2};flagged=set().union(*signals.values());amounts={r[0]:F(r[3]) for r in rows}
check(n+':signal identities',[(s['entity_type'],s['entity_id'],s['claim_ids']) for s in a['signals']],[(t,e,sorted(c)) for (t,e),c in signals.items()],'claims §2,outcomes §2 common repairer exclusion')
for s in a['signals']:check(n+':signal amount '+s['entity_id'],s['claimed_amount'],sum(amounts[c] for c in s['claim_ids']),'claims §2')
check(n+':union ids',a['flagged_claim_ids'],sorted(flagged),'claims §2');check(n+':unique exposure',a['unique_flagged_claimed_amount'],sum(amounts[c] for c in flagged),'claims §2');check(n+':mature count',a['mature_flagged_outcomes'],2,'outcomes §1');check(n+':pending count',a['pending_or_unknown_flagged'],1,'outcomes §1');check(n+':confirmed fraction',a['confirmed_share_among_mature_flagged'],F(1,2),'outcomes §1')
for w,expo,days in [('May',F(1000),31),('June',F(1200),30)]:
 ids={r[0] for r in rows if r[1]==w};native=next(z for z in a['window_rates'] if z['window_id']==w)
 for k,v in {'claims':len(ids),'flagged_claims':len(ids&flagged),'exposure':expo,'days':days,'claim_rate_per_exposure':F(len(ids))/expo,'flagged_claim_fraction':F(len(ids&flagged),len(ids)),'claims_per_day':F(len(ids),days)}.items():check(n+':'+w+' '+k,native[k],v,'claims §§1–2')
check(n+':fraud boundary',a['fraud_determination'],'not_made','request.md')
# Market conduct exact calendar math; R4 remains unknown even though receipt date exists.
n='insurance-market-conduct-reviewer';d=out(n);a=d['results'];D=datetime.date.fromisoformat
for row,(start,end,assessment) in zip(a['control_observations'],[('2026-06-02','2026-06-07','observed_within_target'),('2026-06-03','2026-06-10','observed_exception'),('2026-09-10','2026-09-18','observed_exception'),('2026-09-12',None,'not_evaluable')]):
 check(n+':days '+row['record_id'],row['observed'],F((D(end)-D(start)).days) if end else None,'sample §§1–2 and profile §3');check(n+':assessment '+row['record_id'],row['assessment'],assessment,'same')
for k,v in {'numerator':F(8+2),'denominator':F(100+50),'ratio':F(8+2,100+50)}.items():check(n+':population '+k,a['population_metrics'][0][k],v,'metrics §1 disjoint complete partitions')
check(n+':partial',d['completeness'],'partial','sample §2');check(n+':no extrapolation',a['sample_extrapolation'],'not_performed','sample §1 purposive design');check(n+':no legal opinion',a['compliance_opinion'],'not_made','profile §3')
# Audit amounts independently extracted and final integer half-up rounding.
n='insurance-premium-audit-reviewer';d=out(n);a=d['results'];pay=raw(n,'payroll');man=raw(n,'manual');ct=raw(n,'control');warehouse=money(pay,r'PAY-W\$([0-9.]+)');office=money(pay,r'PAY-O\$([0-9.]+)');rates=re.findall(r'rate\$([0-9.]+) per\$([0-9]+) payroll, (?:combined )?modifier([0-9.]+)',man);assert len(rates)==2
premia=[x/F(unit)*F(rate)*F(mod.rstrip('.')) for x,(rate,unit,mod) in zip([warehouse,office],rates)];manual=sum(premia);fixed=money(man,r'fixed\$([0-9.]+)');minimum=money(man,r'minimum\$([0-9.]+)');unrounded=max(manual+fixed,minimum);cents=unrounded*100;rounded=F((cents.numerator*2+cents.denominator)//(2*cents.denominator),100);deposit=money(ct,r'deposit premium([0-9.]+)');reported=money(ct,r'audited premium([0-9.]+)')
for i,x in enumerate(premia):check(n+f':row{i}',a['exposure_schedule'][i]['unrounded_premium'],x,'manual §1,payroll §1')
for k,v in {'manual_premium':manual,'audited_premium':rounded,'deposit_adjustment':rounded-deposit,'reconciliation_difference':rounded-reported}.items():check(n+':'+k,a[k],v,'manual §2,control §1')
check(n+':known exception',d['status'],'needs-review','control §1')
# Commissions independent raw rate/splits, original event link and sign.
n='insurance-producer-compensation-reconciler';d=out(n);a=d['results'];ag=raw(n,'agreement');ev=raw(n,'events');ct=raw(n,'reported');rate=money(ag,r'rate([0-9.]+)%')/100;splits={p:F(pct)/100 for p,pct in re.findall(r'producer(P\d+) ([0-9]+)%',ag)};amounts=[F(x.rstrip('.')) for x in re.findall(r'commissionable ?(?:received premium)?USD([0-9.]+)',ev)];assert len(amounts)==2,amounts;frac=money(ag,r'authorizes([0-9]+)%')/100;gross=[amounts[0]*rate,amounts[1]*rate,-amounts[0]*rate*frac];controls={p:F(v.rstrip('.')) for p,v in re.findall(r'(P\d+) ([0-9.]+)',ct)}
for i,g in enumerate(gross):
 check(n+f':event{i} gross',a['event_ledger'][i]['gross'],g,'events §§1–2,agreement §§1–2')
 for p,s in splits.items():check(n+f':event{i} split '+p,a['event_ledger'][i]['producer_allocations'][p],g*s,'agreement §1')
for p,s in splits.items():
 net=sum(gross)*s;check(n+':net '+p,a['net_earned_by_producer'][p],net,'events §§1–2,agreement §§1–2');check(n+':break '+p,a['reconciliation_differences'][p],net-controls[p],'reported §1')
check(n+':known exception',d['status'],'needs-review','reported §1')
report={'method':'Independent exact rational arithmetic from raw text/explicit source transcription. No imports of native calculation code. Repeating decimal comparison uses relative/absolute tolerance1e-25; finite monetary calculations are exact. Raw identity/units/bases/unknowns reviewed manually against mapping and documented source locators.','count':len(checks),'passed':sum(c['pass'] for c in checks),'failed':[c for c in checks if not c['pass']],'checks':checks};(R/'independent-checks.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='checks'},indent=2))
assert all(c['pass'] for c in checks)
