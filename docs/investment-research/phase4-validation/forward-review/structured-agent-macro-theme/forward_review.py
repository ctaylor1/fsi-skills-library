import copy,hashlib,json,os,subprocess,sys
from pathlib import Path
ROOT=Path('/Users/taylor/DevRepo/Skills/fsi-skills-library');OUT=Path('/private/tmp/ir-phase4-structured-forward-macro-theme-20261020')
KNOWN='2026-02-15T12:00:00Z'
def context(request,day,cutoff):
 refs=[{'source_id':'fresh-synthetic','locator':'independent synthetic fixture inventory, rows1-9'}]
 return {'request_id':request,'purpose':'internal-research','audience':'internal-review','subject':{'type':'economy','id':'FRESH-ECONOMY'},'as_of':day,'use_on':day,'knowledge_cutoff':cutoff,'information_barrier':'public-side','unresolved_issues':[],
  'sources':[{'source_id':'fresh-synthetic','version':'1','kind':'model','locator':'independent synthetic fixture, not authenticated economic releases','known_at':KNOWN,'subject_ids':['FRESH-ECONOMY'],'permission_status':'supplied-allowed','classification':'public','permitted_audiences':['internal-review'],'permitted_purposes':['internal-research']}], 'evidence_refs':refs}
def cite(d,**kw):return dict(kw,known_at=d['knowledge_cutoff'],evidence_refs=copy.deepcopy(d['evidence_refs']))
def save(name,d):
 p=OUT/(name+'.json');p.write_text(json.dumps(d,indent=2,allow_nan=False)+'\n');return p
transcripts=[]
def run(skill,script,path,extra=()):
 cmd=[sys.executable,'-B',str(ROOT/'skills/investment-research'/skill/'scripts'/script),str(path),*map(str,extra)]
 env=dict(os.environ);env.pop('PYTHONPATH',None);env.pop('PYTHONHOME',None)
 r=subprocess.run(cmd,capture_output=True,text=True,env=env);transcripts.append({'command':cmd,'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr});return r

def pipeline(skill,name,d):
 original=save(name+'-input',d);r=run(skill,'validate_input.py',original);assert r.returncode==0,r.stdout
 r=run(skill,'calculate_or_transform.py',original);assert r.returncode==0,r.stdout
 output=json.loads(r.stdout);outpath=save(name+'-output',output);r=run(skill,'validate_output.py',outpath,('--input',original));assert r.returncode==0,r.stdout
 return output
m=context('fresh-macro-early','2026-03-20','2026-03-20T16:00:00Z')
m['series_inventory_complete']=True;m['requested_series_ids']=['fresh-real-index']
m['series']=[{'series_id':'fresh-real-index','label':'Fresh synthetic monthly real activity index','geography':'FRESH-ECONOMY','frequency':'monthly','measure_kind':'index','unit':'index','price_basis':'real','price_base':'2025=100','seasonal_adjustment':'seasonally-adjusted','annualization':'period-level','observations':[
 {'observation_id':'jan-first','period_end':'2026-01-31','release_at':'2026-02-15T12:00:00Z','vintage_id':'first-Jan','value':120,'evidence_refs':m['evidence_refs']},
 {'observation_id':'feb-first','period_end':'2026-02-28','release_at':'2026-03-15T12:00:00Z','vintage_id':'first-Feb','value':123,'evidence_refs':m['evidence_refs']},
 {'observation_id':'feb-revised','period_end':'2026-02-28','release_at':'2026-04-15T12:00:00Z','vintage_id':'revised-Feb','value':124.5,'evidence_refs':m['evidence_refs']},
 {'observation_id':'feb-future-revision','period_end':'2026-02-28','release_at':'2026-05-15T12:00:00Z','vintage_id':'future-Feb','value':125.7,'evidence_refs':m['evidence_refs']}]}]
m['calculations']=[{'calculation_id':'fresh-growth','series_id':'fresh-real-index','from_period':'2026-01-31','to_period':'2026-02-28','operation':'percent-change'}, {'calculation_id':'fresh-annualized','series_id':'fresh-real-index','from_period':'2026-01-31','to_period':'2026-02-28','operation':'annualized-percent-change'}]
m['outlooks']=[];m['research_questions']=[{'question_id':'fresh-growth-question','question':'How does the selected revision affect measured growth?','required_calculation_ids':['fresh-growth','fresh-annualized'],'interpretation':'Supplied real activity increased on the comparable monthly base; annualization is a convention, not a prediction.','counter_evidence':'A single volatile monthly change and revisions do not establish a persistent regime.'}]
mo=pipeline('macroeconomic-researcher','macro-early',m)
late=copy.deepcopy(m);late.update(request_id='fresh-macro-late',as_of='2026-04-20',use_on='2026-04-20',knowledge_cutoff='2026-04-20T16:00:00Z')
lo=pipeline('macroeconomic-researcher','macro-late',late)

t=context('fresh-theme','2026-10-20','2026-10-20T16:00:00Z');t['theme_id']='fresh-higher-yields';t['driver_observations']=[]
t['hypothesis']={'statement':'Higher relative yields could pressure bond and equity prices while supporting USD in the stated quote.','driver':'parallel relative yield rise','transmission':'Discount rates pressure local valuations; relative policy yields may support USD, conditional on unchanged cash-flow and risk assumptions.','horizon_date':'2027-04-20'}
t['evidence']=[cite(t,evidence_id='fresh-support',role='support',statement='Supplied duration and sensitivities describe a conditional discount-rate and relative-yield channel.'),cite(t,evidence_id='fresh-counter',role='counter',statement='Higher earnings or risk-premium compression may offset discount pressure; FX depends on relative policies and funding flows.')]
t['coverage']={'required_asset_classes':['rates','equity','fx'],'inventory_complete':True}
t['falsifiers']=[{'test_id':'fresh-falsifier','description':'Earnings expansion offsets discount pressure despite higher yields.','monitor':'Compare fresh earnings revisions with relative yields.','due_on':'2027-04-20','status':'not-tested','known_at':None,'evidence_refs':[]}]
t['scenarios']=[cite(t,scenario_id='fresh-100bp',label='Conditional100basis-point parallel relative yield rise',horizon_date='2027-04-20',assumptions=['Supplied fixed sensitivities and parallel move; no convexity, carry, repricing path or coefficient estimation.'],shocks=[{'driver_id':'relative-yield','value':100,'unit':'basis-point'}])]
t['exposures']=[]
for identity,asset,method,sensitivity in [('fresh-bond','rates','modified-duration',6.2),('fresh-equity','equity','linear',-.035),('fresh-fx','fx','linear',.012)]:
 row=cite(t,exposure_id=identity,asset_class=asset,instrument_id=identity+'-instrument',method=method,driver_id='relative-yield',sensitivity=sensitivity,shock_unit='basis-point',response_unit='percent-price-change',mechanism='Conditional discount and relative-yield transmission; all other assumptions held fixed.',limitations=['Synthetic supplied sensitivity; no empirical causal or market-liquidity assurance.'])
 if asset=='fx':row['quote_convention']='EUR per USD'
 t['exposures'].append(row)
to=pipeline('cross-asset-theme-researcher','theme',t)
save('command-transcripts',transcripts)
hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for skill in ('macroeconomic-researcher','cross-asset-theme-researcher') for p in sorted((ROOT/'skills/investment-research'/skill).rglob('*')) if p.is_file() and '__pycache__' not in p.parts}
save('reviewed-package-hashes',hashes)
print(json.dumps({'macro_early':mo['results'],'macro_late':lo['results'],'theme':to['results']},indent=2))
