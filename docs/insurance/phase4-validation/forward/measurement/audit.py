import json,pathlib,decimal,datetime,hashlib
P=pathlib.Path('/tmp/insurance-p4-forward-measurement');D=decimal.Decimal;raw=json.loads((P/'raw-evidence.json').read_text());checks=[]
def eq(name,a,b):
 assert a==b,(name,a,b);checks.append({'check':name,'actual':str(a),'expected':str(b),'passed':True})
def output(stem,repair=False):return json.loads((P/('repairs' if repair else '')/(stem+'-output.json')).read_text())
a=output('architecture-complete')['results'];eq('architecture costs from ARC-17',D(a['supplied_period_cost']),sum(D(c[-1]) for c in raw['architecture']['components']));eq('scoped 640 <= 700 fit',a['requirement_fit'][0]['meets'],True)
c=raw['automation']['cases'];base=sum(D(x[1]) for x in c)/len(c);cand=sum(D(x[2]) for x in c)/len(c);o=output('automation-complete')['results'];eq('paired baseline mean',D(o['observed_means']['baseline_human_minutes']),base);eq('paired candidate includes adverse P3',D(o['observed_means']['candidate_human_minutes']),cand)
for s,n in zip(raw['automation']['scenarios'],o['scenarios']):
 _,vol,eligible,wage,cash,fixed,impl=s;volume=D(str(vol))*D(str(eligible));hours=volume*(base-cand)/60;nonlabor=volume*(sum(D(x[3])-D(x[4]) for x in c)/len(c));net=hours*D(str(wage))*D(str(cash))+nonlabor-D(str(fixed));eq(s[0]+' hours',D(n['capacity_hours']),hours);eq(s[0]+' cash',D(n['annual_cash_net']),net);eq(s[0]+' no positive payback',n['simple_payback_months'],None)
c=raw['data']['cases'];o=output('data-complete')['results'];eq('coverage preserves unmatched cases',D(o['provider_coverage']),D(sum(x[1] for x in c))/len(c));eq('observed outcome reduction from supplied costs',D(o['observed_outcome_cost_reduction']),sum(D(x[5])-D(x[6]) for x in c))
for mode,col in [('baseline',3),('augmented',4)]:
 counts={'tp':0,'tn':0,'fp':0,'fn':0}
 for row in c:counts[('t' if row[col]==row[2] else 'f')+('p' if row[col] else 'n')]+=1
 eq(mode+' confusion', {k:o['confusion_matrices'][mode][k] for k in counts},counts)
r=raw['operations'];dt=lambda x:datetime.datetime.fromisoformat(x.replace('Z','+00:00'));start,end=dt(r['start']),dt(r['end']);completed=[e for e in r['episodes'] if e[3]=='completed' and start<=dt(e[2])<end];dur=[D(str((dt(e[2])-dt(e[1])).total_seconds()/3600)) for e in completed];o=output('operations-unknown-open-cost',True)['results'];eq('queue counts',o['queue_counts'],{'opening':2,'arrivals':3,'completed':2,'cancelled':1,'closing':2});eq('completed mean',D(o['mean_elapsed_hours']),sum(dur)/len(dur));eq('nearest rank p95',D(o['p95_elapsed_hours_nearest_rank']),max(dur));eq('completed costs only',D(o['cost_per_completed']),sum(D(e[4]) for e in completed)/len(completed));eq('completed labor only',D(o['human_minutes_per_completed']),sum(D(e[5]) for e in completed)/len(completed));eq('same-window utilization',D(o['labor_utilization']),D(r['worked_hours'])/D(r['available_hours']));eq('mismatched snapshot not reconciled',output('operations-imperfect',True)['results']['snapshot_reconciled'],False)
for f in sorted((P/'repairs').glob('*-output.json')):
 d=json.loads(f.read_text());inp=json.loads((P/'repairs'/f.name.replace('-output.json','-input.json')).read_text());eq(f.name+' original source retained',d['source_document'],inp)
 for key,value in {'action_taken':False,'human_review_required':True,'approval':'not_requested','execution':'not_performed'}.items():eq(f.name+' '+key,d[key],value)
eq('unresolved projection retains license scope',output('data-unknown-projection',True)['results']['license_usable_for_stated_purpose'],True);eq('unresolved projection withholds annual net',output('data-unknown-projection',True)['results']['projected_annual_net'],None);eq('leakage still blocks observed comparison',output('data-imperfect',True)['results']['confusion_matrices'],None)
(P/'arithmetic-source-authority-audit.json').write_text(json.dumps({'checks':checks,'total':len(checks),'all_passed':True},indent=2)+'\n');print(len(checks),'checks passed')
