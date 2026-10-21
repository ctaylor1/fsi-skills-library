from analysis_contract import validate_base, number, require, rows, unique, references, finish
from datetime import date

def basis(d, keys=('currency','unit','accounting_basis','consolidation_scope','period_id')):
    for k in keys:
        require(isinstance(d.get(k),str) and bool(d[k].strip()) and d[k].strip().lower() not in ('unknown','unspecified','n/a'),k+' must identify a known basis')
def refs(d,row,label):
    references(d,row.get('evidence_refs',[]),label)

def validate_document(doc):
    validate_base(doc,subject_types=('sector','universe','issuer')); require(doc.get('schema_version')=='ir-phase2/1.0','Phase 2 schema required'); basis(doc)
    require(doc.get('primary_method') in ('top_down','bottom_up'),'primary method required'); require(doc.get('segment_coverage') in ('complete','partial','unknown'),'segment coverage required'); require(isinstance(doc.get('segments_disjoint'),bool),'segments_disjoint declaration required')
    td=doc.get('top_down'); require(isinstance(td,dict),'top_down required')
    for k in ('total_market','sam_ratio','som_ratio'):number(td.get(k),k,minimum=0)
    require(td['sam_ratio']<=1 and td['som_ratio']<=1,'ratios exceed one');refs(doc,td,'top-down evidence')
    segments=rows(doc.get('segments'),'segments',nonempty=True);unique(segments,'segment_id','segments')
    for s in segments:
        for k in ('units','price_per_unit','attach_rate','capture_rate'):number(s.get(k),k,minimum=0)
        require(s['attach_rate']<=1 and s['capture_rate']<=1,'segment rates exceed one'); require(s.get('unit_denominator')==doc.get('price_denominator') and isinstance(s.get('unit_denominator'),str) and bool(s['unit_denominator'].strip()),'price/unit denominator mismatch');refs(doc,s,'segment sizing')
    shocks=rows(doc.get('sensitivity_shocks',[]),'sensitivity_shocks');unique(shocks,'shock_id','shocks')
    for s in shocks:
        require(s.get('target') in ('top_down.total_market',)+tuple(x['segment_id']+'.'+k for x in segments for k in ('units','price_per_unit')),'unsupported sensitivity driver');number(s.get('factor'),'factor',minimum=0)

def compute(doc):
    validate_document(doc);td=doc['top_down'];issues=[]
    if not td.get('evidence_refs') or any(not s.get('evidence_refs') for s in doc['segments']):
        return finish(doc,'market-sizing-builder',None,issues=['quantitative sizing input evidence missing; analytical projection withheld'])
    def levels(tam,sam,som):return {'tam':tam,'sam':sam,'som':som}
    top=levels(td['total_market'],td['total_market']*td['sam_ratio'],td['total_market']*td['sam_ratio']*td['som_ratio']);details=[]
    for s in doc['segments']:
        tam=s['units']*s['price_per_unit'];sam=tam*s['attach_rate'];som=sam*s['capture_rate'];details.append({'segment_id':s['segment_id'],**levels(tam,sam,som)})
        if not s.get('evidence_refs'):issues.append(s['segment_id']+': evidence missing')
    bottom={k:sum(x[k] for x in details) for k in ('tam','sam','som')};reconciliation=[]
    for k in top:
        denom=max(abs(top[k]),abs(bottom[k]));reconciliation.append({'level':k,'top_down':top[k],'bottom_up':bottom[k],'difference':top[k]-bottom[k],'relative_gap':abs(top[k]-bottom[k])/denom if denom else 0})
    if not td.get('evidence_refs'):issues.append('top-down evidence missing')
    if not doc['segments_disjoint']:issues.append('bottom-up segment overlap unresolved')
    if doc['segment_coverage']!='complete':issues.append('bottom-up coverage '+doc['segment_coverage'])
    sensitivities=[]
    for s in doc.get('sensitivity_shocks',[]):
        changed=dict(top) if s['target']=='top_down.total_market' else dict(bottom)
        if s['target']=='top_down.total_market': changed={k:v*s['factor'] for k,v in top.items()}
        else:
            segid,_=s['target'].rsplit('.',1);original=next(x for x in details if x['segment_id']==segid);changed={k:bottom[k]+original[k]*(s['factor']-1) for k in bottom}
        sensitivities.append({'shock_id':s['shock_id'],'target':s['target'],'factor':s['factor'],'method':'top_down' if s['target'].startswith('top_down.') else 'bottom_up','levels':changed,'scope':'one driver at a time; no correlated scenario or integrated model rerun'})
    return finish(doc,'market-sizing-builder',{'basis':{k:doc[k] for k in ('currency','unit','accounting_basis','consolidation_scope','period_id')},'top_down':top,'bottom_up':bottom,'segment_detail':details,'reconciliation':reconciliation,'reported':top if doc['primary_method']=='top_down' else bottom,'primary_method':doc['primary_method'],'sensitivity':sensitivities,'limitations':['Both approaches use supplied boundaries and evidence; independence is not authenticated','Sensitivity changes only the selected arithmetic driver; overlap and scope gaps remain unresolved']},issues=issues,lineage=[{'formula':'TAM = units × price_per_unit; SAM = TAM × attach_rate; SOM = SAM × capture_rate; top-down ratios applied in sequence'}])
