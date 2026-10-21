from analysis_contract import validate_base, number, require, rows, unique, references, finish
from datetime import date

def basis(d, keys=('currency','unit','accounting_basis','consolidation_scope','period_id')):
    for k in keys:
        require(isinstance(d.get(k),str) and bool(d[k].strip()) and d[k].strip().lower() not in ('unknown','unspecified','n/a'),k+' must identify a known basis')
def refs(d,row,label):
    references(d,row.get('evidence_refs',[]),label)

SECTIONS=('business_overview','key_financials','ownership','management','trading_data','transactions')
def validate_document(doc):
    validate_base(doc); require(doc.get('schema_version')=='ir-phase2/1.0','Phase 2 schema required')
    req=doc.get('required_sections'); require(isinstance(req,list) and bool(req) and len(set(req))==len(req) and all(x in SECTIONS for x in req),'invalid required sections')
    observations=rows(doc.get('observations'),'observations'); unique(observations,'observation_id','observations')
    for o in observations:
        require(o.get('section') in SECTIONS,'invalid observation section'); require(isinstance(o.get('metric'),str) and bool(o['metric'].strip()),'metric required')
        number(o.get('value'),'observation value',nullable=True); number(o.get('scale',1),'scale',minimum=0); require(o.get('scale',1)>0,'scale must be positive'); basis(o)
        if o['metric']=='employees' and o.get('value') is not None: number(o['value'],'employee count',minimum=0)
        require(isinstance(o.get('period_end'),str) and len(o['period_end'])==10,'period_end required'); date.fromisoformat(o['period_end']); require(o['period_end']<=doc['as_of'],'future observation period')
        refs(doc,o,'profile observation')
    for c in rows(doc.get('claims',[]),'claims'):
        require(c.get('section') in SECTIONS,'invalid claim section'); require(c.get('kind') in ('reported_fact','management_assertion','interpretation'),'invalid profile claim kind'); require(isinstance(c.get('text'),str) and bool(c['text'].strip()),'claim text required'); refs(doc,c,'profile claim')

def compute(doc):
    validate_document(doc); issues=[]; included=[]; withheld=[]; coverage={s:0 for s in doc['required_sections']}
    for o in doc['observations']:
        if o.get('value') is None or not o.get('evidence_refs'):
            withheld.append({'observation_id':o['observation_id'],'reason':'value or evidence missing'}); issues.append(o['observation_id']+': value or evidence missing'); continue
        included.append(o); coverage[o['section']]=coverage.get(o['section'],0)+1
    claims=[]
    for c in doc.get('claims',[]):
        if c.get('evidence_refs'): claims.append(c); coverage[c['section']]=coverage.get(c['section'],0)+1
        else: issues.append(c['section']+': unsourced claim withheld')
    gaps=[s for s in doc['required_sections'] if coverage.get(s,0)==0]; issues += [s+': required profile section incomplete' for s in gaps]
    revenue=[o for o in included if o['metric']=='revenue']; employees=[o for o in included if o['metric']=='employees']; productivity=[]
    for r in revenue:
        matches=[e for e in employees if all(e[k]==r[k] for k in ('period_id','period_end','consolidation_scope')) and e['unit']=='persons' and number(e['value'],'employees')>0]
        if len(matches)==1 and r['unit']=='currency': productivity.append({'period_id':r['period_id'],'revenue_per_employee':number(r['value'],'revenue')*r.get('scale',1)/(number(matches[0]['value'],'employees')*matches[0].get('scale',1)),'currency':r['currency'],'evidence_refs':r['evidence_refs']+matches[0]['evidence_refs']})
    return finish(doc,'company-profile-builder',{'observations':included,'claims':claims,'withheld_observations':withheld,'section_counts':coverage,'missing_sections':gaps,'quantified_profile':{'revenue_per_employee':productivity},'scope':'Cited supplied profile inventory with scaled currency/employee productivity; no factual retrieval or investment recommendation'},issues=issues,lineage=[{'formula':'revenue_per_employee = revenue × currency_scale / (employees × count_scale)','period_id':x['period_id']} for x in productivity])
