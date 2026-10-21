"""Reproducible conjunctive screens with explicit missing, stale and basis exclusions."""
from datetime import date
from analysis_contract import validate_base, number, require, rows, unique, references, finish

OPS={'gte':lambda x,y:x>=y,'lte':lambda x,y:x<=y,'gt':lambda x,y:x>y,'lt':lambda x,y:x<y,'eq':lambda x,y:x==y}
def validate_document(doc):
    validate_base(doc,subject_types=('universe','sector'))
    require(isinstance(doc.get('max_age_days'),int) and not isinstance(doc['max_age_days'],bool) and doc['max_age_days']>=0,'max_age_days must be a nonnegative integer')
    filters=rows(doc.get('filters'),'filters',nonempty=True); unique(filters,'filter_id','filters')
    for f in filters:
        require(f.get('operator') in OPS,'unsupported filter operator'); number(f.get('threshold'),'threshold')
        for k in ('metric','unit','currency','accounting_basis','consolidation_scope','period_id'): require(isinstance(f.get(k),str) and bool(f[k].strip()) and f[k].strip().lower() not in ('unknown','unspecified','n/a'),'filter '+k+' known basis required')
    securities=rows(doc.get('universe'),'universe',nonempty=True); unique(securities,'security_id','universe')
    for s in securities:
        require(isinstance(s.get('issuer_id'),str) and bool(s['issuer_id'].strip()),'issuer_id required')
        require(isinstance(s.get('metrics'),dict),'metrics must be an object')
        for metric,m in s['metrics'].items():
            require(isinstance(m,dict),'metric record must be object'); number(m.get('value'),'metric value',nullable=True)
            for k in ('unit','currency','accounting_basis','consolidation_scope','period_id'): require(isinstance(m.get(k),str) and bool(m[k].strip()) and m[k].strip().lower() not in ('unknown','unspecified','n/a'),'metric '+k+' known basis required')
            require(isinstance(m.get('observed_on'),str) and len(m['observed_on'])==10,'observed_on must be date'); date.fromisoformat(m['observed_on'])
            references(doc,m.get('evidence_refs',[]),'metric evidence')
            byid={x['source_id']:x for x in doc['sources']}
            for ref in m.get('evidence_refs',[]): require(s['issuer_id'] in byid[ref['source_id']]['subject_ids'],'metric source issuer identity mismatch')

def compute(doc):
    validate_document(doc); asof=date.fromisoformat(doc['as_of']); results=[]; issues=[]
    for s in doc['universe']:
        checks=[]
        for f in doc['filters']:
            m=s['metrics'].get(f['metric']); reason=None; passed=None
            if m is None or m.get('value') is None: reason='missing-value'
            elif not m.get('evidence_refs'): reason='missing-evidence'
            elif any(m[k]!=f[k] for k in ('unit','currency','accounting_basis','consolidation_scope','period_id')): reason='incomparable-basis'
            elif (asof-date.fromisoformat(m['observed_on'])).days<0: reason='future-observation'
            elif (asof-date.fromisoformat(m['observed_on'])).days>doc['max_age_days']: reason='stale-observation'
            else: passed=OPS[f['operator']](number(m['value'],'metric'),number(f['threshold'],'threshold')); reason='passes' if passed else 'fails-threshold'
            checks.append({'filter_id':f['filter_id'],'passed':passed,'reason':reason})
        state='excluded' if any(x['passed'] is False for x in checks) else ('not-evaluable' if any(x['passed'] is None for x in checks) else 'included')
        if state=='not-evaluable': issues.append(s['security_id']+': missing, stale or incomparable screening data')
        results.append({'security_id':s['security_id'],'issuer_id':s['issuer_id'],'status':state,'checks':checks})
    return finish(doc,'research-universe-screener',{'screen_logic':'all supplied filters must pass; missing is not zero','results':results,'included_security_ids':[r['security_id'] for r in results if r['status']=='included'],'excluded_security_ids':[r['security_id'] for r in results if r['status']=='excluded'],'not_evaluable_security_ids':[r['security_id'] for r in results if r['status']=='not-evaluable'],'counts':{k:sum(r['status']==k for r in results) for k in ('included','excluded','not-evaluable')},'scope':'Supplied universe only; no survivor-bias, delisting or population-completeness assurance'},issues=issues,lineage=[{'filter_id':f['filter_id'],'metric':f['metric'],'operator':f['operator'],'threshold':f['threshold']} for f in doc['filters']])
