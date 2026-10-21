from __future__ import annotations
import math, importlib.util
from pathlib import Path
from analysis_contract import validate_base, number, require, rows, unique, references, finish
from native_integrity import canonical_hash
SKILL='kpi-segment-bridge-builder'
def local(filename):
    spec=importlib.util.spec_from_file_location('_phase2_'+SKILL.replace('-','_')+'_'+filename.replace('.','_'),Path(__file__).with_name(filename));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def context(doc):
    validate_base(doc)
    require(doc.get('schema_version')=='ir-phase2/1.0','Phase2 schema_version required')
    require(doc.get('issuer_type')=='nonfinancial-corporate','supported annual operating method requires nonfinancial-corporate; no bank/insurer/REIT fallback')
    for k in ('accounting_basis','consolidation_scope'):require(isinstance(doc.get(k),str) and doc[k].strip(),k+' required')

def native_valid(doc,key):
    errors,warnings=local('validate_input.py')._validate_phase1(doc.get(key))
    require(not errors,'; '.join(errors))

def validate_document(doc):
    validate_base(doc);require(doc.get('schema_version')=='ir-phase2/1.0','Phase2 schema required')
    from datetime import date
    for k in ('prior_period_end','current_period_end'):date.fromisoformat(doc.get(k))
    require(doc['prior_period_end']<doc['current_period_end']<=doc['as_of'],'historical period order invalid')
    for k in ('currency','units','accounting_basis','consolidation_scope','mapping_version'):require(isinstance(doc.get(k),str) and bool(doc[k].strip()),k+' required')
    require(isinstance(doc.get('reported_totals'),dict) and set(doc['reported_totals'])=={'prior_revenue','current_revenue','prior_ebit','current_ebit'},'reported_totals requires exactly the four supported metrics')
    for k in ('prior_revenue','current_revenue','prior_ebit','current_ebit'):number(doc['reported_totals'].get(k),k)
    mappings=rows(doc.get('mappings'),'mappings',nonempty=True);unique(mappings,'mapping_id','mappings');known={r['mapping_id']:r for r in mappings}
    segments=rows(doc.get('segments'),'segments',nonempty=True);unique(segments,'segment_id','segments')
    for row in segments:
        for k in ('prior_revenue','current_revenue','prior_ebit','current_ebit'):number(row.get(k),k)
        require(row['prior_revenue']>=0 and row['current_revenue']>=0,'segment revenues must be nonnegative')
        require(row.get('mapping_id') in known,'missing segment mapping')
        mapping=known[row['mapping_id']]
        require(mapping.get('status')=='reviewed-supplied','mapping review remains supplied, explicit reviewed-supplied required')
        start=date.fromisoformat(mapping.get('effective_from'));end=date.fromisoformat(mapping.get('effective_to'))
        require(start<=date.fromisoformat(doc['prior_period_end']) and end>=date.fromisoformat(doc['current_period_end']),'mapping must cover both periods or use an explicitly recast comparable basis')
        references(doc,row.get('evidence_refs'),'segment evidence');references(doc,mapping.get('evidence_refs'),'mapping evidence')
    number(doc.get('tolerance'),'tolerance',minimum=0)
    return []

def compute(doc):
    validate_document(doc);segments=[];issues=[];checks=[]
    for row in doc['segments']:
        a=row['prior_revenue'];b=row['current_revenue'];delta=row['current_ebit']-row['prior_ebit']
        if a>0 and b>0:
            prior=row['prior_ebit']/a;current=row['current_ebit']/b
            mix=(b-a)*prior;margin=b*(current-prior);unallocated=delta-mix-margin
        else:prior=current=mix=margin=None;unallocated=delta;issues.append('Zero revenue prevents margin decomposition: '+row['segment_id'])
        segments.append({'segment_id':row['segment_id'],'mapping_id':row['mapping_id'],'prior_margin':prior,'current_margin':current,'ebit_change':delta,'revenue_effect':mix,'margin_effect':margin,'unallocated':unallocated,'evidence_refs':row['evidence_refs']})
    for key,target in doc['reported_totals'].items():
        total=sum(s[key] for s in doc['segments']);residual=total-target;ok=abs(residual)<=doc['tolerance'];checks.append({'metric':key,'segment_sum':total,'reported_total':target,'residual':residual,'within_tolerance':ok})
        if not ok:issues.append('Segment totals fail consolidated reconciliation: '+key)
    return finish(doc,SKILL,{'currency':doc['currency'],'units':doc['units'],'segments':segments,'consolidated_checks':checks,'mapping_version':doc['mapping_version'],'all_reconciled':all(x['within_tolerance'] for x in checks),'method_scope':'Historical segment EBIT decomposition using explicit comparable mappings; missing denominators remain unallocated; no forecast or inferred normalization.'},issues=issues,lineage=[{'formula':'EBIT delta = (current revenue - prior revenue)*prior margin + current revenue*(current margin-prior margin) + unallocated'}])
