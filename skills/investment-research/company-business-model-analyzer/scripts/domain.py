"""Revenue, contribution economics, unit drivers and named exposure analysis."""
from analysis_contract import validate_base, number, require, rows, unique, references, finish

def validate_document(doc):
    validate_base(doc)
    for k in ('currency','unit','accounting_basis','consolidation_scope','period_id'): require(isinstance(doc.get(k),str) and bool(doc[k].strip()) and doc[k].strip().lower() not in ('unknown','unspecified','n/a'),k+' known basis required')
    number(doc.get('consolidated_revenue'),'consolidated_revenue',nullable=True,minimum=0)
    segments=rows(doc.get('segments'),'segments',nonempty=True); unique(segments,'segment_id','segments')
    for s in segments:
        require(isinstance(s.get('driver'),str) and bool(s['driver'].strip()),'segment driver required')
        for k in ('revenue','variable_cost','units'): number(s.get(k),k,nullable=True,minimum=0)
        references(doc,s.get('evidence_refs',[]),'segment evidence')
    exposures=rows(doc.get('customer_exposures',[]),'customer_exposures'); unique(exposures,'customer_id','customer_exposures')
    for x in exposures: number(x.get('revenue'),'customer revenue',nullable=True,minimum=0); references(doc,x.get('evidence_refs',[]),'customer evidence')
    require(doc.get('segment_coverage') in ('complete','partial','unknown'),'segment_coverage declaration required')
    for claim in rows(doc.get('business_claims',[]),'business_claims'):
        require(claim.get('kind') in ('reported_fact','management_assertion','analyst_forecast','interpretation'),'unsupported claim kind')
        require(isinstance(claim.get('text'),str) and bool(claim['text'].strip()),'claim text required'); references(doc,claim.get('evidence_refs',[]),'claim evidence')

def compute(doc):
    validate_document(doc); issues=[]; total=number(doc.get('consolidated_revenue'),'revenue',nullable=True); detail=[]; segment_sum=0; sum_known=True
    for s in doc['segments']:
        rev=number(s.get('revenue'),'revenue',nullable=True); cost=number(s.get('variable_cost'),'cost',nullable=True); units=number(s.get('units'),'units',nullable=True)
        if not s.get('evidence_refs'): rev=cost=units=None
        if rev is None: sum_known=False
        else: segment_sum+=rev
        if not s.get('evidence_refs'): issues.append(s['segment_id']+': evidence missing')
        detail.append({'segment_id':s['segment_id'],'driver':s['driver'],'revenue':rev,'share_of_consolidated_revenue':rev/total if rev is not None and total and total>0 else None,'contribution_profit':rev-cost if rev is not None and cost is not None else None,'contribution_margin':(rev-cost)/rev if rev and cost is not None else None,'revenue_per_unit':rev/units if rev is not None and units and units>0 else None,'evidence_refs':s.get('evidence_refs',[])})
    residual=total-segment_sum if total is not None and sum_known else None
    if residual is None: issues.append('segment reconciliation unavailable: missing consolidated or segment revenue')
    elif abs(residual)>1e-8: issues.append('segment revenue does not reconcile to consolidated revenue')
    if doc['segment_coverage']!='complete': issues.append('segment coverage '+doc['segment_coverage'])
    exposures=[]
    for x in doc.get('customer_exposures',[]):
        r=number(x.get('revenue'),'customer revenue',nullable=True)
        if not x.get('evidence_refs'): r=None
        exposures.append({'customer_id':x['customer_id'],'revenue':r,'share_of_consolidated_revenue':r/total if r is not None and total and total>0 else None,'evidence_refs':x.get('evidence_refs',[])})
        if r is not None and total is not None and r>total: issues.append(x['customer_id']+': exposure exceeds consolidated revenue')
        if not x.get('evidence_refs'): issues.append(x['customer_id']+': evidence missing')
    claims=[c for c in doc.get('business_claims',[]) if c.get('evidence_refs')]
    if len(claims)!=len(doc.get('business_claims',[])): issues.append('unsourced business claims withheld')
    return finish(doc,'company-business-model-analyzer',{'basis':{k:doc[k] for k in ('currency','unit','accounting_basis','consolidation_scope','period_id')},'segments':detail,'segment_reconciliation':{'supplied_segment_revenue':segment_sum if sum_known else None,'consolidated_revenue':total,'residual':residual,'status':'reconciled-for-supplied-scope' if residual is not None and abs(residual)<=1e-8 and doc['segment_coverage']=='complete' else 'review-required'},'named_customer_exposures':exposures,'business_claims':claims,'limitations':['Contribution profit excludes unprovided fixed costs, taxes, capital costs and allocation effects','Named exposures are not a complete customer concentration measure; no moat or pricing-power conclusion is inferred']},issues=issues,lineage=[{'formula':'contribution_profit = revenue - variable_cost; share = segment_revenue / consolidated_revenue; revenue_per_unit = revenue / units','segment_id':s['segment_id']} for s in doc['segments']])
