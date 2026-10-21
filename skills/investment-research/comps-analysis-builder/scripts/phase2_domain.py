from __future__ import annotations
import math, importlib.util
from pathlib import Path
from analysis_contract import validate_base, number, require, rows, unique, references, finish
from native_integrity import canonical_hash
SKILL='comps-analysis-builder'
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
    subject=doc.get('valuation_subject')
    require(isinstance(subject,dict),'valuation_subject required for per-share analysis')
    for k in ('security_id','share_class','share_count_basis'):
        require(isinstance(subject.get(k),str) and bool(subject[k].strip()),'valuation_subject '+k+' required')
    require(doc['subject']['type']!='security' or subject['security_id']==doc['subject']['id'],'valuation security identity mismatch')
    profile=doc.get('issuer_type');methods={'bank':{'P/E','P/B','P/TBV'},'insurer':{'P/E','P/B'},'reit':{'P/FFO','P/AFFO'}}
    require(profile in methods,'specialist equity comps support explicit bank, insurer or REIT profiles')
    require(doc.get('multiple') in methods[profile],'multiple not supported for selected issuer profile')
    for k in ('currency','units','accounting_basis','consolidation_scope','metric_period_end','metric_definition'):
        require(isinstance(doc.get(k),str) and bool(doc[k].strip()),k+' required')
    from datetime import date
    require(date.fromisoformat(doc['metric_period_end'])<=date.fromisoformat(doc['as_of']),'historical metric period cannot be future')
    require(number(doc.get('diluted_shares'),'diluted_shares',minimum=0)>0,'positive diluted shares required')
    number(doc.get('subject_denominator_per_share'),'subject denominator per share')
    peers=rows(doc.get('peers'),'peers',nonempty=True);unique(peers,'issuer_id','peers')
    require(isinstance(doc.get('minimum_peers'),int) and not isinstance(doc['minimum_peers'],bool) and doc['minimum_peers']>=1,'minimum_peers integer >=1 required')
    maxage=doc.get('max_price_age_days');require(isinstance(maxage,int) and not isinstance(maxage,bool) and maxage>=0,'max_price_age_days integer >=0 required')
    for row in peers:
        number(row.get('share_price'),'share_price',minimum=0);number(row.get('denominator_per_share'),'denominator_per_share')
        for k in ('currency','units','accounting_basis','consolidation_scope','metric_period_end','metric_definition'):require(row.get(k)==doc[k],'peer financial basis mismatch: '+k)
        price=date.fromisoformat(row.get('price_date'));require(price<=date.fromisoformat(doc['as_of']),'future price prohibited')
        references(doc,row.get('evidence_refs'),'peer sources')
    return []

def compute(doc):
    import statistics
    from datetime import date
    validate_document(doc);peers=[];issues=[];eligible=[]
    for row in doc['peers']:
        age=(date.fromisoformat(doc['as_of'])-date.fromisoformat(row['price_date'])).days
        reason='stale-price' if age>doc['max_price_age_days'] else 'nonpositive-denominator' if row['denominator_per_share']<=0 else None
        multiple=None if reason else row['share_price']/row['denominator_per_share']
        peers.append({'issuer_id':row['issuer_id'],'multiple':multiple,'exclusion_reason':reason,'price_age_days':age})
        if multiple is not None:eligible.append(multiple)
        else:issues.append(row['issuer_id']+': '+reason)
    sufficient=len(eligible)>=doc['minimum_peers'];median=statistics.median(eligible) if sufficient else None
    if not sufficient:issues.append('Insufficient eligible financial-sector peers')
    implied=None if median is None or doc['subject_denominator_per_share']<=0 else median*doc['subject_denominator_per_share']
    if doc['subject_denominator_per_share']<=0:issues.append('Subject denominator nonpositive; implied equity unavailable')
    return finish(doc,SKILL,{'valuation_subject':doc['valuation_subject'],'issuer_type':doc['issuer_type'],'multiple':doc['multiple'],'metric_definition':doc['metric_definition'],'peers':peers,'eligible_count':len(eligible),'median_multiple':median,'implied_value_per_share':implied,'implied_equity_value':None if implied is None else implied*doc['diluted_shares'],'enterprise_value':None,'method_scope':'Matched supplied per-share financial-sector metrics; no EV-based bank valuation, regulatory capital, FFO normalization or peer selection assurance.'},issues=issues,lineage=[{'formula':'median(price / positive per-share denominator) * subject denominator; equity = implied per share * diluted shares'}])
