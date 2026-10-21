import copy,json,runpy
from pathlib import Path
p=Path('/private/tmp/ir-phase4-structured-forward-macro-theme-20261020');v=runpy.run_path(str(p/'forward_review.py'))
run,save,pipeline=v['run'],v['save'],v['pipeline'];m,late,t=v['m'],v['late'],v['t'];checks=[]
def close(a,b):assert abs(a-b)<1e-9,(a,b)
e=json.loads((p/'macro-early-output.json').read_text());l=json.loads((p/'macro-late-output.json').read_text());th=json.loads((p/'theme-output.json').read_text())
close(e['results']['calculations'][0]['value'],2.5);close(l['results']['calculations'][0]['value'],3.75)
close(e['results']['calculations'][1]['value'],((123/120)**12-1)*100);close(l['results']['calculations'][1]['value'],((124.5/120)**12-1)*100)
assert e['results']['calculations'][0]['to_observation_id']=='feb-first';assert l['results']['calculations'][0]['to_observation_id']=='feb-revised'
close(l['results']['revisions'][0]['value_change'],1.5)
assert '125.7' not in json.dumps(e) and '125.7' not in json.dumps(l)
assert any(r['observation_id']=='feb-future-revision' for r in l['results']['excluded_observations'])
checks.append({'case':'macro-two-cutoffs-independent-growth-annualization-revision-future-value-exclusion','result':'PASS'})
responses={r['exposure_id']:r for r in th['results']['scenario_responses']}
close(responses['fresh-bond']['value'],-6.2);close(responses['fresh-equity']['value'],-3.5);close(responses['fresh-fx']['value'],1.2)
assert responses['fresh-fx']['quote_convention']=='EUR per USD'
for key in ('causality_established','probabilities_estimated','portfolio_allocation_proposed'):assert th['results'][key] is False
checks.append({'case':'theme-units-duration-linear-fx-quote-and-no-causality-allocation','result':'PASS'})
rejects=[]
d=copy.deepcopy(m);d['series'][0]['observations'].append(copy.deepcopy(d['series'][0]['observations'][0]));rejects.append(('macro-duplicate-observation','macroeconomic-researcher',d))
d=copy.deepcopy(m);d['series'][0]['observations'][0]['period_end']='2026-01-30';rejects.append(('macro-nonperiod-end','macroeconomic-researcher',d))
d=copy.deepcopy(m);d['series'][0]['price_base']='unknown';rejects.append(('macro-unknown-real-base','macroeconomic-researcher',d))
d=copy.deepcopy(m);d['series'][0]['observations'][0]['value']=True;rejects.append(('macro-boolean-number','macroeconomic-researcher',d))
d=copy.deepcopy(t);del d['exposures'][2]['quote_convention'];rejects.append(('theme-missing-fx-quote','cross-asset-theme-researcher',d))
d=copy.deepcopy(t);d['exposures'][0]['sensitivity']=-6.2;rejects.append(('theme-negative-modified-duration','cross-asset-theme-researcher',d))
d=copy.deepcopy(t);d['exposures'][0]['weight']=.5;rejects.append(('theme-unsupported-portfolio-weight','cross-asset-theme-researcher',d))
d=copy.deepcopy(t);d['scenarios'][0]['probability']=.6;rejects.append(('theme-unsupported-probability','cross-asset-theme-researcher',d))
d=copy.deepcopy(t);d['evidence'][0]['known_at']='2026-10-21T00:00:00Z';rejects.append(('theme-future-evidence','cross-asset-theme-researcher',d))
for name,skill,d in rejects:
 path=save(name+'-input',d);r=run(skill,'validate_input.py',path)
 assert r.returncode!=0 and 'ERROR' in r.stdout and 'Traceback' not in r.stderr,(name,r.stdout,r.stderr)
 checks.append({'case':name,'result':'PASS-rejected'})
# Real source publication timing is gated separately from the synthetic model-release selection above.
d=copy.deepcopy(late);d['sources'][0]['known_at']='2026-04-21T00:00:00Z'
# This source postdates every row, so the input is rejected rather than permitting a retroactive release.
path=save('macro-future-source-input',d);r=run('macroeconomic-researcher','validate_input.py',path)
assert r.returncode!=0 and 'ERROR' in r.stdout
checks.append({'case':'macro-source-postdating-row-cannot-claim-availability','result':'PASS-rejected'})
d=copy.deepcopy(m);d['series'][0]['observations'][0]['value']=None;o=pipeline('macroeconomic-researcher','macro-null-endpoint',d)
assert o['results']['calculations'][0]['value'] is None and o['status']=='partial'
checks.append({'case':'macro-explicit-missing-endpoint-no-zero','result':'PASS-null-partial'})
d=copy.deepcopy(t);d['scenarios'][0]['shocks'][0]['unit']='percent'
path=save('theme-unit-mismatch-input',d);r=run('cross-asset-theme-researcher','validate_input.py',path)
if r.returncode==0:
 c=run('cross-asset-theme-researcher','calculate_or_transform.py',path)
 if c.returncode==0:
  o=json.loads(c.stdout);assert all(x['value'] is None for x in o['results']['scenario_responses']) and o['status']=='partial'
 else:assert 'ERROR' in c.stdout and 'Traceback' not in c.stderr
else:assert 'ERROR' in r.stdout
checks.append({'case':'theme-unit-mismatch-no-implicit-bp-percent-conversion','result':'PASS-no-numerical-projection'})
d=copy.deepcopy(t);d['scenarios'][0]['shocks'][0]['value']=2000;o=pipeline('cross-asset-theme-researcher','theme-large-shock',d)
assert o['results']['scenario_responses'][0]['value'] is None and o['status']=='partial'
checks.append({'case':'theme-duration-impossible-price-response-withheld','result':'PASS-null-partial'})
d=copy.deepcopy(t);d['coverage']['required_asset_classes'].append('credit');d['evidence']=[d['evidence'][0]]
o=pipeline('cross-asset-theme-researcher','theme-coverage-countergap',d)
assert 'credit' in o['results']['coverage']['missing_asset_classes'] and o['status']=='partial'
assert any('counter' in x.lower() for x in o['unresolved_issues'])
checks.append({'case':'theme-missing-counterevidence-and-required-asset-gap','result':'PASS-partial'})
d=copy.deepcopy(t);f=d['falsifiers'][0];f.update(status='observed',known_at=d['knowledge_cutoff'],evidence_refs=d['evidence_refs'])
o=pipeline('cross-asset-theme-researcher','theme-falsifier-observed',d)
assert o['status']=='partial' and any('falsifier' in x.lower() for x in o['unresolved_issues'])
checks.append({'case':'theme-observed-falsifier-reassessment-remains-open','result':'PASS-partial'})
for name,skill,source in [('macro','macroeconomic-researcher',m),('theme','cross-asset-theme-researcher',t)]:
 d=copy.deepcopy(source);d['sources'][0]['permission_status']='denied';o=pipeline(skill,name+'-denied',d)
 assert o['results'] is None and o['calculation_lineage']==[] and o['source_register']==[]
 checks.append({'case':name+'-denied-source-no-projection','result':'PASS-withheld'})
 o=copy.deepcopy(e if name=='macro' else th);o['authority_granted']=True;op=save(name+'-tampered-output',o);ip=save(name+'-original-input',source)
 r=run(skill,'validate_output.py',op,('--input',ip));assert r.returncode!=0 and 'ERROR' in r.stdout
 checks.append({'case':name+'-tampered-output-reconstruction','result':'PASS-rejected'})
save('independent-checks',checks);save('command-transcripts',v['transcripts']);print(len(checks),'fresh/adverse checks passed')
