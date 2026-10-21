"""Bounded structured research QA; no text entailment or publication clearance."""
from __future__ import annotations
import math
from analysis_contract import validate_base, number, require, rows, unique, references, finish
from research_runtime import text, strings, only, temporal, eligible_time, calendar_date

SKILL='research-quality-reviewer'
CHECKS={'sections','claim_evidence','arithmetic','contradictions','comparability','risks','disclosures'}
BASIS=('currency','units','accounting_basis','consolidation_scope','period_end','measure')


def ids(value,label,nonempty=False):
    strings(value,label,nonempty)
    return value


def validate_document(doc):
    validate_base(doc,subject_types=None)
    require(doc.get('requested_action','review')=='review','only review action is supported')
    scope=doc.get('review_scope');require(isinstance(scope,dict),'review_scope object required')
    only(scope,'required_checks required_sections required_claim_ids required_arithmetic_ids required_risks required_disclosures inventory_complete','review_scope')
    require(set(ids(scope.get('required_checks'),'required_checks',True))<=CHECKS,'unsupported review check')
    for key in ('required_sections','required_claim_ids','required_arithmetic_ids','required_risks','required_disclosures'):
        ids(scope.get(key),key)
    require(isinstance(scope.get('inventory_complete'),bool),'inventory_complete must explicitly describe supplied inventory')
    # A request cannot quietly declare a requirement and exclude the check that tests it.
    for key,check in (('required_sections','sections'),('required_claim_ids','claim_evidence'),('required_arithmetic_ids','arithmetic'),('required_risks','risks'),('required_disclosures','disclosures')):
        require(not scope[key] or check in scope['required_checks'],key+' requires '+check+' review')
    packet=doc.get('packet');require(isinstance(packet,dict),'packet object required')
    only(packet,'packet_id sections claims arithmetic_checks contradictions comparability_groups risks disclosures','packet')
    require(text(packet.get('packet_id')),'packet_id required')
    claims=rows(packet.get('claims'),'claims');unique(claims,'claim_id','claims');known={c['claim_id'] for c in claims}
    require(len(claims)<=5000,'claim inventory exceeds bounded 5000 claim scope')
    for c in claims:
        only(c,'claim_id kind subject_id text known_at evidence_refs value basis forecast rationale','claim')
        require(c.get('kind') in ('fact','forecast','judgment'),'claim kind must distinguish fact, forecast or judgment')
        require(text(c.get('subject_id')) and text(c.get('text')),'claim subject_id and text required')
        temporal(c.get('known_at'));references(doc,c.get('evidence_refs'),'claim evidence_refs')
        if 'value' in c:
            number(c['value'],'claim value',nullable=True)
            b=c.get('basis');require(isinstance(b,dict),'numeric claim requires explicit basis')
            only(b,' '.join(BASIS),'claim basis')
            for key in BASIS:require(text(b.get(key)) and b[key].strip().lower() not in ('unknown','not-provided','unavailable'),'known claim basis '+key+' required')
            calendar_date(b['period_end'])
        elif 'basis' in c:raise ValueError('basis requires a supplied numeric value or explicit null')
        if c['kind']=='forecast':
            forecast=c.get('forecast');require(isinstance(forecast,dict),'forecast requires horizon and explicit assumptions')
            only(forecast,'horizon assumptions','forecast');calendar_date(forecast.get('horizon'));ids(forecast.get('assumptions'),'forecast assumptions',True)
        else:require('forecast' not in c,'forecast metadata requires forecast kind')
        if c['kind']=='judgment':require(text(c.get('rationale')),'judgment requires an explicit rationale')
        else:require('rationale' not in c,'judgment rationale requires judgment kind')
    for field,idkey in (('sections','section_id'),('risks','risk_id'),('disclosures','disclosure_id'),('comparability_groups','group_id')):
        group=rows(packet.get(field),field);unique(group,idkey,field)
        for row in group:
            only(row,idkey+' claim_ids',field);ids(row.get('claim_ids'),field+' claim_ids')
            require(set(row['claim_ids'])<=known,field+' references unknown claim')
            if field=='comparability_groups':require(len(row['claim_ids'])>=2,'comparability group needs at least two claims')
    checks=rows(packet.get('arithmetic_checks'),'arithmetic_checks');unique(checks,'check_id','arithmetic_checks')
    for row in checks:
        only(row,'check_id operation operand_claim_ids reported_claim_id tolerance','arithmetic check')
        require(row.get('operation') in ('sum','difference','ratio','percent-change'),'unsupported arithmetic operation')
        ids(row.get('operand_claim_ids'),'operand_claim_ids',True)
        require(set(row['operand_claim_ids'])<=known and row.get('reported_claim_id') in known,'arithmetic references unknown claim')
        require(row['reported_claim_id'] not in row['operand_claim_ids'],'reported claim cannot be its own operand')
        require(len(row['operand_claim_ids'])>=2 if row['operation']=='sum' else len(row['operand_claim_ids'])==2,'arithmetic operand count invalid')
        number(row.get('tolerance'),'arithmetic tolerance',minimum=0)
    conflicts=rows(packet.get('contradictions'),'contradictions');unique(conflicts,'contradiction_id','contradictions')
    for row in conflicts:
        only(row,'contradiction_id claim_ids description status resolution_evidence_refs','contradiction')
        ids(row.get('claim_ids'),'contradiction claim_ids',True)
        require(len(row['claim_ids'])>=2 and set(row['claim_ids'])<=known,'contradiction needs at least two known claims')
        require(text(row.get('description')),'contradiction description required')
        require(row.get('status') in ('open','resolved-supplied'),'contradiction status unsupported')
        references(doc,row.get('resolution_evidence_refs',[]),'resolution evidence')
        if row['status']=='resolved-supplied':require(bool(row.get('resolution_evidence_refs')),'supplied resolution needs cited evidence')
    return []


def compute(doc):
    validate_document(doc)
    scope=doc['review_scope'];packet=doc['packet'];selected=set(scope['required_checks']);claims={c['claim_id']:c for c in packet['claims']};sources={s['source_id']:s for s in doc['sources']}
    findings=[];arithmetic=[];coverage=[]
    def finding(check,key,message,severity='high',adjudication='open'):
        findings.append({'finding_id':f'qa-{len(findings)+1}','severity':severity,'check':check,'subject_id':key,'message':message,'adjudication_status':adjudication})
    if not scope['inventory_complete']:finding('scope','inventory','Supplied packet inventory is explicitly incomplete.','critical')
    if not claims: finding('scope','claims','No claims supplied; review cannot establish requested research coverage.','critical')
    for issue in doc.get('unresolved_issues',[]):finding('inherited','inherited-issue','Inherited unresolved issue: '+issue,'high','inherited-open')
    # Explicit requirements detect deletions; an empty inventory never passes a required item.
    for field,idkey,requirements,check in (('sections','section_id','required_sections','sections'),('risks','risk_id','required_risks','risks'),('disclosures','disclosure_id','required_disclosures','disclosures')):
        if check not in selected:continue
        indexed={x[idkey]:x for x in packet[field]}
        for key in scope[requirements]:
            present=key in indexed and bool(indexed[key]['claim_ids'])
            coverage.append({'requirement_type':check,'requirement_id':key,'covered':present})
            if not present:finding(check,key,'Requested '+check+' coverage is missing or has no supporting claims.','critical')
        for key,row in indexed.items():
            if not row['claim_ids']:finding(check,key,'Supplied '+check+' row has no supporting claims.')
    if 'claim_evidence' in selected:
        allowed={doc['subject']['id'],doc['subject'].get('issuer_id')}
        for key in scope['required_claim_ids']:
            covered=key in claims;coverage.append({'requirement_type':'claim','requirement_id':key,'covered':covered})
            if not covered:finding('claim_evidence',key,'Requested claim is absent from supplied packet.','critical')
        for key,c in claims.items():
            if c['subject_id'] not in allowed:finding('claim_evidence',key,'Claim subject does not match requested subject.','critical')
            if not c['evidence_refs']:finding('claim_evidence',key,'Claim has no supplied evidence references.')
            if eligible_time(c['known_at'],doc['knowledge_cutoff']) is not True:finding('claim_evidence',key,'Claim knowledge time is after cutoff or has incompatible precision.','critical')
            for ref in c['evidence_refs']:
                source=sources[ref['source_id']]
                if c['subject_id'] not in source['subject_ids']:finding('claim_evidence',key,'Cited source does not cover this claim subject.','critical')
                if eligible_time(source['known_at'],c['known_at']) is not True:finding('claim_evidence',key,'Claim predates cited evidence or uses incompatible knowledge precision.','critical')
            if c['kind']=='fact' and c.get('basis',{}).get('period_end',doc['as_of'])>doc['as_of']:
                finding('claim_evidence',key,'Future economic period labeled as fact; classify the supplied forecast explicitly.','critical')
            if c['kind']=='forecast' and c['forecast']['horizon']<c.get('basis',{}).get('period_end',c['forecast']['horizon']):
                finding('claim_evidence',key,'Forecast horizon precedes its numeric period end.')
        # Numeric findings do not prove textual entailment or the validity of a conclusion.
        for c in packet['claims']:
            if c['kind']=='judgment':finding('claim_evidence',c['claim_id'],'Judgment rationale and textual evidence entailment require human assessment.','review','human-assessment-required')
    if 'arithmetic' in selected:
        indexed={x['check_id']:x for x in packet['arithmetic_checks']}
        for key in scope['required_arithmetic_ids']:
            covered=key in indexed;coverage.append({'requirement_type':'arithmetic','requirement_id':key,'covered':covered})
            if not covered:finding('arithmetic',key,'Requested arithmetic check is missing.','critical')
        for row in packet['arithmetic_checks']:
            operand=[claims[k] for k in row['operand_claim_ids']];reported=claims[row['reported_claim_id']];reason=None;expected=None
            if any(c.get('value') is None for c in operand+[reported]):reason='Missing numeric input; no zero substitution is permitted.'
            elif any(any(c.get('basis',{}).get(k)!=operand[0].get('basis',{}).get(k) for k in BASIS if k not in ({'period_end'} if row['operation']=='percent-change' else set())|{'measure'}) for c in operand[1:]):reason='Operand currency, units, period or accounting basis differ.'
            elif row['operation']=='percent-change' and (operand[0]['basis']['measure']!=operand[1]['basis']['measure'] or operand[0]['basis']['period_end']<operand[1]['basis']['period_end']):reason='Percent change requires the same measure with current period at or after the base period.'
            elif row['operation'] in ('sum','difference') and any(reported.get('basis',{}).get(k)!=operand[0].get('basis',{}).get(k) for k in BASIS if k!='measure'):reason='Reported result basis differs from additive operands.'
            elif row['operation'] in ('ratio','percent-change'):
                expected_units='ratio' if row['operation']=='ratio' else 'percent'
                rb=reported.get('basis',{});ob=operand[0].get('basis',{})
                if rb.get('currency')!='not-applicable' or rb.get('units')!=expected_units or any(rb.get(k)!=ob.get(k) for k in ('accounting_basis','consolidation_scope','period_end')):reason='Ratio output requires explicit dimensionless currency, units and matching date/accounting scope.'
                elif operand[1]['value']==0:reason='Denominator is zero; ratio is unavailable.'
            if reason is None:
                vals=[c['value'] for c in operand]
                try:
                    expected=math.fsum(vals) if row['operation']=='sum' else vals[0]-vals[1] if row['operation']=='difference' else vals[0]/vals[1] if row['operation']=='ratio' else (vals[0]/vals[1]-1)*100
                    if not math.isfinite(expected):reason='Arithmetic result is nonfinite.';expected=None
                except (OverflowError,ZeroDivisionError):reason='Arithmetic result is unavailable.'
            residual=reported.get('value')-expected if expected is not None else None
            if residual is not None and not math.isfinite(residual):reason='Arithmetic residual is nonfinite.';residual=None
            good=reason is None and residual is not None and abs(residual)<=row['tolerance']
            arithmetic.append({'check_id':row['check_id'],'operation':row['operation'],'operand_claim_ids':row['operand_claim_ids'],'reported_claim_id':row['reported_claim_id'],'recomputed_value':expected,'reported_value':reported.get('value'),'residual':residual,'within_tolerance':good,'unavailable_reason':reason})
            if not good:finding('arithmetic',row['check_id'],reason or 'Reported arithmetic differs from independent recomputation beyond supplied tolerance.','critical')
    if 'contradictions' in selected:
        for row in packet['contradictions']:
            finding('contradictions',row['contradiction_id'],'Contradictory claims remain unresolved for this review; supplied resolution requires separate adjudication.','high','supplied-resolution-pending' if row['status']=='resolved-supplied' else 'open')
    if 'comparability' in selected:
        for group in packet['comparability_groups']:
            compared=[claims[k] for k in group['claim_ids']]
            if any(c.get('basis') is None for c in compared):finding('comparability',group['group_id'],'Comparability group contains claims without numeric basis.')
            elif any(c['basis']!=compared[0]['basis'] for c in compared[1:]):finding('comparability',group['group_id'],'Supplied numeric bases differ; no normalization is assumed.')
    severities={f['severity'] for f in findings};readiness='blocked' if severities.intersection({'critical','high'}) else 'review-required' if findings else 'complete-for-supplied-scope'
    results={'packet_id':packet['packet_id'],'reviewed_checks':sorted(selected),'excluded_checks':sorted(CHECKS-selected),'coverage':coverage,'arithmetic_results':arithmetic,'findings':findings,'findings_count':len(findings),'readiness':readiness,'publication_approved':False,'model_approved':False,'native_producer_validation':'not-performed-by-this-method','textual_entailment':'human-review-required','inventory_assurance':'supplied-not-authenticated','scope':'Structured supplied packet metadata, requested coverage and declared arithmetic only; no hidden-claim discovery, textual truth assessment, source authentication or institutional sign-off.'}
    issues=[f["severity"]+': '+f["check"]+'/'+f["subject_id"]+' - '+f["message"] for f in findings]
    return finish(doc,SKILL,results,issues=issues,lineage=[{'method':'Independent declared arithmetic recomputation and explicit requested inventory coverage; retained source timing and basis checks.','arithmetic_checks_evaluated':len(arithmetic)}])

# unexpected local drift
