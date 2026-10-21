"""Bounded supplied-input review. No source authentication or business action."""
from decimal import Decimal
from foundation_contract import (D,ratio,date_value,exact,validate_common,validate_actual_date,validate_referenced_sources,finish,cli_compute)
from native_integrity import canonical_hash

@exact
def analyze(d):
    issues=[];accepted=[];omitted=0;target=d['intended_audience'];seen=set()
    if target not in {'internal-review','institutional-client','retail-client','public'}:raise ValueError('explicit intended audience required')
    def scope_supported(source):
        return source and all(key not in source or source[key]==d[key] for key in ('object_id','currency'))
    for claim in d['claims']:
        if claim['claim_id'] in seen:raise ValueError('duplicate claim id')
        seen.add(claim['claim_id']);source=next((s for s in d['sources'] if s['source_ref']==claim['source_ref']),None)
        allowed=scope_supported(source) and target in source.get('permitted_audiences',[]) and source.get('approval_status')=='approved'
        allowed=allowed and source.get('claims',{}).get(claim['claim_id'])==claim['content']
        if not allowed:omitted+=1;issues.append('proposed claim withheld: audience, approval or exact source support unavailable');continue
        if any(word in claim['content'].lower() for word in ['guaranteed return','risk-free profit','cannot lose']):omitted+=1;issues.append('promissory claim withheld for professional review');continue
        if claim['kind']=='performance':
            p=claim['performance'];gross=D(p['gross_return']);net=D(p['net_return']) if p.get('net_return') is not None else None
            if not p.get('period_start') or not p.get('period_end') or date_value(p['period_start'])>=date_value(p['period_end']):raise ValueError('performance period invalid')
            validate_actual_date(d,p['period_end'],claim['source_ref'])
            if date_value(p['period_end'])>date_value(d['as_of']):raise ValueError('future actual performance')
            if source.get('performance',{}).get(claim['claim_id'])!=p:omitted+=1;issues.append('performance data lacks exact source support');continue
            if net is None or not p.get('fee_basis') or p.get('net_period_start')!=p['period_start'] or p.get('net_period_end')!=p['period_end']:
                omitted+=1;issues.append('performance withheld for net/fee/period review');continue
            if p.get('hypothetical') is True:omitted+=1;issues.append('hypothetical performance requires separate appropriateness and assumptions review');continue
        elif claim['kind']!='factual':raise ValueError('unsupported claim class')
        accepted.append({'claim_id':claim['claim_id'],'content':claim['content'],'source_ref':claim['source_ref']})
    disclosures=[]
    for required in d['required_disclosures']:
        row=next((r for r in d['disclosures'] if r['id']==required),None)
        source=next((s for s in d['sources'] if row and s['source_ref']==row.get('source_ref')),None)
        if not row or not scope_supported(source) or target not in source.get('permitted_audiences',[]) or source.get('approval_status')!='approved' or source.get('claims',{}).get(row['id'])!=row.get('text'):
            issues.append('required disclosure unavailable: '+required)
        else:disclosures.append({'id':required,'text':row['text'],'source_ref':row['source_ref']})
    return {'supported_claims':accepted,'withheld_count':omitted,'disclosures':disclosures,'intended_audience':target,'publication_authorized':False,'compliance_conclusion':None},issues

SKILL='investment-disclosure-reviewer'
METHOD='approved-source-claim-disclosure-review'
LIMITS=['Internal review packet; source approvals and rights remain supplied assertions.', 'Bounded presentation checks do not determine legal marketing-rule compliance.']
HANDOFFS=['investment-investor-report-builder', 'institutional-proposal-responder']

def validate(doc):
    errors=validate_common(doc)
    if errors:return errors
    errors+=validate_referenced_sources(doc)
    if doc.get('requested_action','review') not in ('review','draft'):errors.append('business execution unsupported')
    if errors:return errors
    try:analyze(doc)
    except (ValueError,TypeError,KeyError,IndexError,ArithmeticError) as exc:errors.append(str(exc))
    return errors

def compute(doc):
    errors=validate(doc)
    if errors:raise ValueError('; '.join(errors))
    results,issues=analyze(doc)
    return finish(doc,SKILL,METHOD,results,issues=issues,limitations=LIMITS,handoffs=HANDOFFS)

if __name__=='__main__':cli_compute(compute)
