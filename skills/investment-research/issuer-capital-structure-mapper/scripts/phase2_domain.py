"""Bounded supplied-evidence research; no source authentication or execution."""
from datetime import date, datetime, timezone
from copy import deepcopy
from statistics import median
from analysis_contract import validate_base, number, require, rows, unique, references, finish

def text(v,label):
    require(isinstance(v,str) and bool(v.strip()),label+' must be a non-empty string')
    return v
def obj(v,label):
    require(isinstance(v,dict),label+' must be an object'); return v
def day(v,label):
    text(v,label); require(len(v)==10,label+' must be YYYY-MM-DD'); return date.fromisoformat(v)
def stamp(v,label):
    text(v,label); require('T' in v,label+' must contain an intraday time')
    d=datetime.fromisoformat(v.replace('Z','+00:00')); require(d.tzinfo is not None,label+' requires timezone'); return d
def flag(v,label):
    require(isinstance(v,bool),label+' must be boolean'); return v
def amount(row,key,nullable=False,minimum=None):
    number(row.get(key),key,nullable=nullable,minimum=minimum); return row.get(key)
def cited(doc,row,label):
    require(isinstance(row.get('evidence_refs'),list) and bool(row['evidence_refs']),label+' requires nonempty evidence_refs')
    references(doc,row.get('evidence_refs'),label+'.evidence_refs')
def field_context(row,label):
    for k in ('currency','unit','accounting_basis','consolidation_scope'): text(row.get(k),label+'.'+k)
    p=obj(row.get('period'),label+'.period'); text(p.get('fiscal_calendar_id'),label+'.fiscal_calendar_id')
    a=day(p.get('start'),label+'.period.start'); b=day(p.get('end'),label+'.period.end'); require(a<=b,label+' period reversed')
def comparable(a,b):
    return all(a.get(k)==b.get(k) for k in ('currency','unit','accounting_basis','consolidation_scope','period'))
def base(doc):
    validate_base(doc,subject_types=('issuer','security'))
    require(doc.get('schema_version')=='ir-phase2/1.0','unsupported Phase 2 schema_version')
def done(doc,skill,result,issues=None,lineage=None):
    if lineage is None: lineage=[{'operation':'Principal sums by exact currency and unit; explicit identity and directed acyclic supplied priority links','input_binding':'complete-original-input-hash','input_fields':sorted(k for k in doc if k not in ('sources','evidence_refs')),'output_fields':sorted(result),'evidence_refs':deepcopy(doc['evidence_refs'])}]
    return finish(doc,skill,result,issues=issues or [],lineage=lineage)

SKILL='issuer-capital-structure-mapper'
def validate_document(doc):
    base(doc); flag(doc.get('instrument_inventory_complete'),'instrument_inventory_complete'); ins=rows(doc.get('instruments'),'instruments',nonempty=True); unique(ins,'instrument_id','instruments')
    for r in ins:
        obj(r,'instrument')
        for k in ('instrument_id','issuer_id','estate_id','security_id','priority_basis','currency','unit','document_id','document_version'): text(r.get(k),'instrument.'+k)
        require(r['issuer_id']==doc['subject'].get('issuer_id',doc['subject']['id']),'instrument issuer differs from declared single-issuer scope')
        amount(r,'principal',nullable=True,minimum=0); amount(r,'coupon_pct',nullable=True,minimum=0)
        if r.get('maturity_date') is not None: day(r['maturity_date'],'maturity_date')
        require(r.get('secured') is None or isinstance(r['secured'],bool),'secured must be boolean or unknown')
        flag(r.get('guarantee_inventory_complete'),'guarantee_inventory_complete'); cited(doc,r,'instrument')
        for key in ('guarantor_ids','collateral_ids'):
            gs=rows(r.get(key),key)
            for g in gs: text(g,key)
            require(len(gs)==len(set(gs)),'duplicate '+key)
    for r in rows(doc.get('priority_links'),'priority_links'):
        obj(r,'priority_link'); text(r.get('senior_instrument_id'),'senior_instrument_id'); text(r.get('junior_instrument_id'),'junior_instrument_id'); text(r.get('basis'),'basis'); cited(doc,r,'priority_link')
        ids={i['instrument_id'] for i in ins}; require(r['senior_instrument_id'] in ids and r['junior_instrument_id'] in ids,'priority link unknown instrument'); require(r['senior_instrument_id']!=r['junior_instrument_id'],'self priority link')
def compute(doc):
    validate_document(doc); issues=[] if doc['instrument_inventory_complete'] else ['supplied issuer instrument inventory incomplete']; groups={}; ids={r['instrument_id']:r for r in doc['instruments']}
    # Priority assertions are a directed acyclic graph, not a legal interpretation.
    graph={k:[] for k in ids}
    for e in doc['priority_links']: graph[e['senior_instrument_id']].append(e['junior_instrument_id'])
    def visit(n,path):
        require(n not in path,'cyclic priority assertions');
        for x in graph[n]: visit(x,path+[n])
    for n in graph: visit(n,[])
    for r in doc['instruments']:
        g=groups.setdefault(r['currency']+'|'+r['unit'],{'currency':r['currency'],'unit':r['unit'],'known_principal':0.,'total_principal':None,'principal_complete':True,'maturity_complete':True,'maturities':[]})
        if r['principal'] is None: g['principal_complete']=False; issues.append(r['instrument_id']+': principal unknown')
        else: g['known_principal']+=r['principal']
        if r.get('maturity_date') is None: g['maturity_complete']=False; issues.append(r['instrument_id']+': maturity unknown')
        g['maturities'].append({'instrument_id':r['instrument_id'],'date':r.get('maturity_date'),'amount':r['principal'],'evidence_refs':r['evidence_refs']})
        if not r['guarantee_inventory_complete']: issues.append(r['instrument_id']+': guarantee inventory incomplete')
        if r['secured'] is None or r['priority_basis']=='unknown': issues.append(r['instrument_id']+': security or legal priority unresolved')
    for g in groups.values(): g['total_principal']=g['known_principal'] if g['principal_complete'] else None; g['maturity_complete']=g['maturity_complete'] and g['principal_complete']
    return done(doc,SKILL,{'instrument_inventory_complete':doc['instrument_inventory_complete'],'issuer_scope':'single-declared-issuer','instruments':deepcopy(doc['instruments']),'currency_unit_groups':list(groups.values()),'priority_links':deepcopy(doc['priority_links']),
        'guarantee_links':[{'instrument_id':r['instrument_id'],'guarantor_ids':r['guarantor_ids'],'inventory_complete':r['guarantee_inventory_complete']} for r in doc['instruments']],
        'legal_priority_established':False,'refinancing_recommendation':'not-made','map_scope':'supplied instrument, estate, security, guarantee and priority assertions'},issues)
