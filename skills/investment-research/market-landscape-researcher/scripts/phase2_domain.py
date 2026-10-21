from analysis_contract import validate_base, number, require, rows, unique, references, finish
from datetime import date

def basis(d, keys=('currency','unit','accounting_basis','consolidation_scope','period_id')):
    for k in keys:
        require(isinstance(d.get(k),str) and bool(d[k].strip()) and d[k].strip().lower() not in ('unknown','unspecified','n/a'),k+' must identify a known basis')
def refs(d,row,label):
    references(d,row.get('evidence_refs',[]),label)

def validate_document(doc):
    validate_base(doc,subject_types=('sector','universe','issuer')); require(doc.get('schema_version')=='ir-phase2/1.0','Phase 2 schema required')
    for k in ('market_definition','geography','period_id','share_basis'): require(isinstance(doc.get(k),str) and bool(doc[k].strip()),k+' required')
    basis(doc,('market_definition','geography','period_id','share_basis'))
    require(doc.get('population_coverage') in ('complete','partial','unknown'),'population coverage required')
    comps=rows(doc.get('competitors',[]),'competitors'); unique(comps,'competitor_id','competitors')
    for c in comps:
        number(c.get('share_pct'),'share_pct',nullable=True,minimum=0); require(c.get('share_pct') is None or c['share_pct']<=100,'share above 100%')
        for k in ('market_definition','geography','period_id','share_basis'): require(isinstance(c.get(k),str) and bool(c[k].strip()),'competitor '+k+' required')
        refs(doc,c,'competitor share')
    for f in rows(doc.get('findings',[]),'findings'):
        require(isinstance(f.get('dimension'),str) and bool(f['dimension'].strip()) and isinstance(f.get('text'),str) and bool(f['text'].strip()),'finding dimension/text required'); refs(doc,f,'landscape finding')

def compute(doc):
    validate_document(doc); accepted=[]; excluded=[]; issues=[]
    for c in doc.get('competitors',[]):
        reasons=[]
        if any(c[k]!=doc[k] for k in ('market_definition','geography','period_id','share_basis')): reasons.append('incomparable-market-share-basis')
        if c['share_pct'] is None or not c.get('evidence_refs'): reasons.append('share-or-evidence-missing')
        if reasons: excluded.append({'competitor_id':c['competitor_id'],'reasons':reasons}); issues.append(c['competitor_id']+': share not comparable')
        else: accepted.append(c)
    shares=sorted([c['share_pct'] for c in accepted],reverse=True); total=sum(shares); require(total<=100+1e-8,'comparable shares exceed 100%')
    tail=max(0,100-total); hhi=sum(s*s for s in shares); complete=doc['population_coverage']=='complete' and not excluded and abs(tail)<1e-8
    if not complete:issues.append('full market concentration not established')
    findings=[f for f in doc.get('findings',[]) if f.get('evidence_refs')]
    if len(findings)!=len(doc.get('findings',[])):issues.append('unsupported landscape findings withheld')
    return finish(doc,'market-landscape-researcher',{'market_scope':{k:doc[k] for k in ('market_definition','geography','period_id','share_basis')},'comparable_competitors':accepted,'excluded_shares':excluded,'named_share_sum_pct':total,'unattributed_tail_pct':tail,'named_cr4_pct':sum(shares[:4]) if shares else None,'named_hhi_lower_bound':hhi if shares else None,'hhi_upper_bound_unknown_tail':hhi+tail*tail if shares else None,'concentration_scope':'complete-supplied-market' if complete else 'named-set-and-unknown-tail-bound','findings':findings,'limitations':['Unknown tail is not allocated or normalized to 100%; no legal market definition or regulatory concentration conclusion','A complete coverage declaration is supplied and not independently verified']},issues=issues,lineage=[{'formula':'named_HHI = sum(share_pct²); upper_bound = named_HHI + unknown_tail_pct²; named_CR4 = sum(four largest named shares)'}])
