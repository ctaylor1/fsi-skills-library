"""Bounded supplied-evidence research; no source authentication or execution."""
from datetime import date, datetime, timezone
from copy import deepcopy
from statistics import median
from fractions import Fraction
from analysis_contract import validate_base, number, require, rows, unique, references, finish
from research_runtime import temporal

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
    if lineage is None: lineage=[{'operation':'Debt/positive EBITDA; (debt-unrestricted cash)/positive EBITDA; EBITDA/positive interest; operating cash flow-capex; FFO/positive debt','input_binding':'complete-original-input-hash','input_fields':sorted(k for k in doc if k not in ('sources','evidence_refs')),'output_fields':sorted(result),'evidence_refs':deepcopy(doc['evidence_refs'])}]
    return finish(doc,skill,result,issues=issues or [],lineage=lineage)

SKILL='issuer-credit-researcher'

CONTEXT_FIELDS=('currency','unit','accounting_basis','consolidation_scope','period')
FINANCIAL_FIELDS=('ebitda','gross_debt','unrestricted_cash','interest_expense','operating_cash_flow','capex','funds_from_operations')

def decimal(value):
    """Exact arithmetic on the finite decimal representation supplied in JSON."""
    return Fraction(str(value))

def optional_context(row,label):
    for key in CONTEXT_FIELDS[:-1]:
        if key in row:text(row[key],label+'.'+key)
    if 'period' in row:field_context({**{k:row.get(k,'missing') for k in CONTEXT_FIELDS[:-1]},'period':row['period']},label)

def context_reasons(row,financials,label):
    reasons=[]
    for key in CONTEXT_FIELDS:
        if key not in row:reasons.append(label+': missing '+key)
        elif row[key]!=financials[key]:reasons.append(label+': '+key+' differs from reported financial context')
    return reasons

def binding_reasons(doc,row,label):
    """Check supplied evidence identity, never claim independent authentication."""
    binding=row.get('source_binding')
    if not isinstance(binding,dict):return [label+': missing source_binding'],None
    keys=('source_id','version','known_at','locator','economic_event_key','subject_issuer_id')
    if any(not isinstance(binding.get(k),str) or not binding[k].strip() for k in keys):
        return [label+': incomplete source-bound economic identity'],None
    sources={s['source_id']:s for s in doc['sources']};source=sources.get(binding['source_id']);reasons=[]
    subject_issuer_id=doc['subject'].get('issuer_id',doc['subject']['id'])
    if binding['subject_issuer_id']!=subject_issuer_id:reasons.append(label+': source_binding subject_issuer_id differs from target issuer')
    if source is None:reasons.append(label+': source_binding source is not registered')
    else:
        if binding['subject_issuer_id'] not in source['subject_ids']:reasons.append(label+': registered source block does not identify target issuer')
        if binding['version']!=source['version']:reasons.append(label+': source_binding version differs from source register')
        if binding['locator']!=source['locator']:reasons.append(label+': source_binding locator differs from registered precise source block')
        try:
            if temporal(binding['known_at'])!=temporal(source['known_at']):reasons.append(label+': source_binding known_at differs from source register')
        except (TypeError,ValueError):reasons.append(label+': source_binding known_at is invalid')
    if not any(ref.get('source_id')==binding['source_id'] and ref.get('locator')==binding['locator'] for ref in row.get('evidence_refs',[])):
        reasons.append(label+': source_binding locator is not cited by the row')
    # Canonical economic identity is independent of document, locator or version.
    # Corroborating documents cannot turn the same event into additive amounts.
    return reasons,(binding['subject_issuer_id'],binding['economic_event_key'])

def citation_identity(refs):
    return {(ref['source_id'],ref['locator']) for ref in refs}

def validate_reconciliation_rows(doc):
    events=rows(doc.get('ebitda_adjustment_events',[]),'ebitda_adjustment_events');unique(events,'ledger_id','ebitda_adjustment_events')
    for event in events:
        optional_context(event,'adjustment event')
        if 'amount' in event:amount(event,'amount')
        if 'evidence_refs' in event:cited(doc,event,'adjustment event')
        components=rows(event.get('components',[]),'event.components');unique(components,'component_id','event.components')
        for component in components:
            amount(component,'amount');cited(doc,component,'adjustment component')
    reconciliation=doc.get('debt_reconciliation')
    if reconciliation is not None:
        obj(reconciliation,'debt_reconciliation');optional_context(reconciliation,'debt_reconciliation')
        if 'evidence_refs' in reconciliation:cited(doc,reconciliation,'debt_reconciliation')
        bridge=rows(reconciliation.get('bridge',[]),'debt_reconciliation.bridge');unique(bridge,'bridge_id','debt_reconciliation.bridge')
        for row in bridge:
            optional_context(row,'debt bridge');amount(row,'amount');cited(doc,row,'debt bridge')
            if 'instrument_ids' in row:
                ids=rows(row['instrument_ids'],'debt bridge.instrument_ids')
                for identifier in ids:text(identifier,'debt bridge.instrument_id')
                require(len(ids)==len(set(ids)),'duplicate debt bridge instrument_id')
    for instrument in doc['instruments']:
        optional_context(instrument,'instrument principal')
        inclusion=instrument.get('debt_inclusion')
        if inclusion is not None:
            obj(inclusion,'instrument.debt_inclusion');optional_context(inclusion,'instrument.debt_inclusion')
            if 'evidence_refs' in inclusion:cited(doc,inclusion,'instrument.debt_inclusion')

def reconcile_adjustments(doc):
    financials=doc['financials'];adjustments=doc.get('ebitda_adjustments',[]);events=doc.get('ebitda_adjustment_events',[]);reasons=[];groups={};identities={};used=set();total=Fraction(0)
    for event in events:
        label='adjustment event '+event['ledger_id'];event_id=event.get('economic_event_id')
        if not isinstance(event_id,str) or not event_id.strip():reasons.append(label+': missing economic_event_id');continue
        groups.setdefault(event_id,[]).append(event)
        reasons.extend(context_reasons(event,financials,label));gaps,identity=binding_reasons(doc,event,label);reasons.extend(gaps)
        if identity is not None:
            if identity in identities:reasons.append(label+': source economic event duplicates '+identities[identity])
            identities[identity]=event_id
        if not isinstance(event.get('event_version'),str) or not event['event_version'].strip():reasons.append(label+': missing event_version')
        if 'amount' not in event:reasons.append(label+': missing signed event amount')
        if event.get('aggregation') not in ('event-total-only','additive-components'):reasons.append(label+': unsupported or missing additive treatment')
        components=event.get('components',[])
        if event.get('aggregation')=='event-total-only' and components:reasons.append(label+': event-total-only cannot also declare additive components')
        if event.get('aggregation')=='additive-components':
            if not components:reasons.append(label+': additive component inventory is missing')
            elif 'amount' in event and sum((decimal(c['amount']) for c in components),Fraction(0))!=decimal(event['amount']):reasons.append(label+': component sum does not equal signed event amount')
    for event_id,candidates in groups.items():
        if len(candidates)!=1:reasons.append(event_id+': multiple ledger candidates or versions for one economic event')
    rows_by_event={}
    for adjustment in adjustments:
        event_id=adjustment.get('economic_event_id');label='adjustment '+adjustment['adjustment_id']
        if not isinstance(event_id,str) or not event_id.strip():reasons.append(label+': missing economic_event_id');continue
        candidates=groups.get(event_id,[])
        if len(candidates)!=1:reasons.append(label+': economic event does not resolve to exactly one ledger entry');continue
        event=candidates[0];used.add(event_id);rows_by_event.setdefault(event_id,[]).append(adjustment)
        if adjustment.get('event_version')!=event.get('event_version') or not adjustment.get('event_version'):reasons.append(label+': event version is missing or conflicting')
    for event_id,event_rows in rows_by_event.items():
        event=groups[event_id][0];label='adjustment event '+event_id;roles=[r.get('aggregation_role') for r in event_rows]
        if roles==['event-total']:
            if event.get('amount') is None or decimal(event_rows[0]['amount'])!=decimal(event['amount']):reasons.append(label+': adjustment differs from signed event total')
            if citation_identity(event_rows[0]['evidence_refs'])!=citation_identity(event.get('evidence_refs',[])):reasons.append(label+': selected total citations differ from event evidence')
        elif all(role=='component' for role in roles) and event.get('aggregation')=='additive-components':
            components={c['component_id']:c for c in event.get('components',[])};seen=set()
            for row in event_rows:
                component_id=row.get('component_id')
                if not isinstance(component_id,str) or component_id not in components:reasons.append(label+': unrecognized component identity');continue
                if component_id in seen:reasons.append(label+': economic component counted under multiple adjustment IDs')
                seen.add(component_id)
                if decimal(row['amount'])!=decimal(components[component_id]['amount']):reasons.append(label+': component amount conflicts with evidence ledger')
                if citation_identity(row['evidence_refs'])!=citation_identity(components[component_id]['evidence_refs']):reasons.append(label+': selected component citations differ from component evidence')
            if seen!=set(components):reasons.append(label+': selected components do not cover the additive event inventory')
        else:reasons.append(label+': repeated total, total/component overlap, or unsupported additive selection')
        if event.get('amount') is not None:total+=decimal(event['amount'])
    if set(groups)!=used:reasons.append('adjustment event ledger contains unresolved or unselected events')
    if adjustments and not events:reasons.append('adjustments lack a source-bound economic event ledger')
    reasons=sorted(set(reasons))
    return {'status':'unavailable' if reasons else 'reconciled','reasons':reasons,
            'signed_adjustment_total':None if reasons else float(total),'events':deepcopy(events),'selected_adjustments':deepcopy(adjustments)},(None if reasons else total)

def reconcile_debt(doc):
    financials=doc['financials'];reasons=[];included=[];excluded=[];principal=Fraction(0);bridge_total=Fraction(0);reconciliation=doc.get('debt_reconciliation');identities={};events=set()
    if reconciliation is None:reasons.append('debt inventory lacks source-bound coverage and principal-to-carrying-value reconciliation');reconciliation={}
    reasons.extend(context_reasons(reconciliation,financials,'debt inventory'))
    gaps,_=binding_reasons(doc,reconciliation,'debt inventory');reasons.extend(gaps)
    if reconciliation.get('inventory_coverage')!='complete-for-supplied-scope':reasons.append('debt inventory coverage is missing or incomplete')
    if not isinstance(reconciliation.get('coverage_description'),str) or not reconciliation['coverage_description'].strip():reasons.append('debt inventory lacks a coverage description')
    for instrument in doc['instruments']:
        label='instrument '+instrument['instrument_id'];inclusion=instrument.get('debt_inclusion') or {};treatment=inclusion.get('treatment')
        if treatment not in ('included','excluded'):reasons.append(label+': explicit debt inclusion/exclusion is missing');continue
        reasons.extend(context_reasons(inclusion,financials,label+' inclusion'))
        if inclusion.get('subject_issuer_id')!=doc['subject'].get('issuer_id',doc['subject']['id']):reasons.append(label+': inclusion target subject_issuer_id is missing or differs from target issuer')
        if not inclusion.get('evidence_refs'):reasons.append(label+': inclusion/exclusion lacks evidence')
        if not isinstance(inclusion.get('reason'),str) or not inclusion['reason'].strip():reasons.append(label+': inclusion/exclusion lacks a scoped reason')
        if treatment=='excluded':excluded.append(instrument['instrument_id']);continue
        included.append(instrument['instrument_id'])
        reasons.extend(context_reasons(instrument,financials,label+' principal'))
        if instrument['currency']!=financials['currency']:reasons.append(label+': instrument principal currency differs from reported debt; FX unsupported')
        if instrument.get('principal_basis')!='contractual-principal':reasons.append(label+': principal measurement basis is missing or unsupported')
        if instrument.get('principal') is None:reasons.append(label+': included principal is missing')
        else:principal+=decimal(instrument['principal'])
    bridge=reconciliation.get('bridge',[])
    if not bridge:reasons.append('debt inventory requires an explicit cited principal-to-carrying-value bridge, including a zero bridge when equal')
    bridged=set()
    for row in bridge:
        label='debt bridge '+row['bridge_id'];reasons.extend(context_reasons(row,financials,label));gaps,identity=binding_reasons(doc,row,label);reasons.extend(gaps)
        event_id=row.get('economic_event_id')
        if not isinstance(event_id,str) or not event_id.strip():reasons.append(label+': economic_event_id is missing')
        elif event_id in events:reasons.append(label+': economic bridge event is counted more than once')
        else:events.add(event_id)
        if identity is not None:
            if identity in identities:reasons.append(label+': source economic bridge event duplicates '+identities[identity])
            identities[identity]=row['bridge_id']
        if row.get('bridge_type')!='principal-to-carrying-value':reasons.append(label+': unsupported or missing measurement bridge basis')
        if not isinstance(row.get('rationale'),str) or not row['rationale'].strip():reasons.append(label+': bridge rationale is missing')
        instrument_ids=row.get('instrument_ids',[])
        if (not instrument_ids and (included or row['amount']!=0)) or not set(instrument_ids)<=set(included):reasons.append(label+': bridge must identify included instruments only')
        bridged.update(instrument_ids)
        bridge_total+=decimal(row['amount'])
    if bridged!=set(included):reasons.append('principal-to-carrying-value bridge does not cover the included instrument inventory')
    reconstructed=principal+bridge_total
    if financials.get('gross_debt') is None:reasons.append('reported gross debt is missing')
    elif reconstructed!=decimal(financials['gross_debt']):reasons.append('included principal plus carrying-value bridge does not equal reported gross debt')
    reasons=sorted(set(reasons))
    return {'status':'unavailable' if reasons else 'reconciled','reasons':reasons,'included_instrument_ids':included,'excluded_instrument_ids':excluded,
            'included_principal_total':float(principal),'carrying_value_bridge_total':float(bridge_total),'reconstructed_gross_debt':float(reconstructed),
            'reported_gross_debt':financials.get('gross_debt'),'inventory_evidence':deepcopy(reconciliation),'instrument_evidence':deepcopy(doc['instruments'])}

def validate_document(doc):
    base(doc); require(doc.get('issuer_profile')=='nonfinancial-corporate','only nonfinancial-corporate EBITDA analysis supported')
    f=obj(doc.get('financials'),'financials'); field_context(f,'financials'); cited(doc,f,'financials')
    cutoff=temporal(doc['knowledge_cutoff'])[1]
    cutoff_date=cutoff.date() if isinstance(cutoff,datetime) else cutoff
    require(day(f['period']['end'],'financials.period.end')<=min(day(doc['as_of'],'as_of'),cutoff_date),
            'financials reported period must end on or before as_of and knowledge_cutoff; forecast/scenario financials unsupported')
    for k in FINANCIAL_FIELDS:
        amount(f,k,nullable=True,minimum=0 if k in ('gross_debt','unrestricted_cash','interest_expense','capex') else None)
    ins=rows(doc.get('instruments'),'instruments',nonempty=True); unique(ins,'instrument_id','instruments')
    for i,r in enumerate(ins):
        obj(r,'instrument');
        for k in ('instrument_id','issuer_id','estate_id','seniority','currency'): text(r.get(k),'instrument.'+k)
        amount(r,'principal',nullable=True,minimum=0); cited(doc,r,'instrument')
        gs=rows(r.get('guarantor_ids'),'guarantor_ids')
        for g in gs: text(g,'guarantor_id')
        require(len(gs)==len(set(gs)),'duplicate guarantor_id')
    adjustments=rows(doc.get('ebitda_adjustments',[]),'ebitda_adjustments')
    unique(adjustments,'adjustment_id','ebitda_adjustments')
    for a in adjustments:
        obj(a,'adjustment'); text(a.get('adjustment_id'),'adjustment_id'); text(a.get('rationale'),'rationale'); amount(a,'amount'); cited(doc,a,'adjustment')
    for r in rows(doc.get('risk_observations',[]),'risk_observations'):
        obj(r,'risk'); text(r.get('risk_id'),'risk_id'); text(r.get('category'),'risk.category'); text(r.get('observation'),'risk.observation'); cited(doc,r,'risk')
    validate_reconciliation_rows(doc)
def compute(doc):
    validate_document(doc)
    # Intake accepts omitted and explicit-null amounts as unknown. Normalize only
    # the local calculation view; retain the exact separately bound original.
    f={**doc['financials'],**{k:doc['financials'].get(k) for k in FINANCIAL_FIELDS}}
    issues=['financials.'+k+': missing evidence; dependent calculations withheld' for k in FINANCIAL_FIELDS if f[k] is None]
    adjustment_reconciliation,adjustment_total=reconcile_adjustments(doc);debt_reconciliation=reconcile_debt(doc)
    issues.extend(adjustment_reconciliation['reasons']);issues.extend(debt_reconciliation['reasons'])
    e=f['ebitda']; adjusted=None if e is None or adjustment_total is None else float(decimal(e)+adjustment_total)
    usable_debt=f['gross_debt'] if debt_reconciliation['status']=='reconciled' else None
    metrics={}
    for label,den in [('reported_ebitda',e),('analyst_adjusted_ebitda',adjusted)]:
        metrics[label]={'ebitda':den,'gross_leverage_x':usable_debt/den if den is not None and den>0 and usable_debt is not None else None,
            'net_leverage_x':(usable_debt-f['unrestricted_cash'])/den if den is not None and den>0 and usable_debt is not None and f['unrestricted_cash'] is not None else None,
            'interest_coverage_x':den/f['interest_expense'] if den is not None and f['interest_expense'] is not None and f['interest_expense']>0 else None}
        if any(v is None for v in metrics[label].values()): issues.append(label+': missing, incomparable or nonpositive evidence; dependent ratios withheld')
    debt=usable_debt; cash_flow={'free_cash_flow':f['operating_cash_flow']-f['capex'] if f['operating_cash_flow'] is not None and f['capex'] is not None else None,
        'ffo_to_debt':f['funds_from_operations']/debt if f['funds_from_operations'] is not None and debt is not None and debt>0 else None}
    if f['funds_from_operations'] is not None and cash_flow['ffo_to_debt'] is None:
        issues.append('cash_flow.ffo_to_debt: reconciled positive gross debt is unavailable; ratio withheld')
    structural=[]; subject=doc['subject'].get('issuer_id',doc['subject']['id'])
    for r in doc['instruments']:
        if r['issuer_id']!=subject and subject not in r['guarantor_ids']:
            structural.append({'instrument_id':r['instrument_id'],'issue':'separate legal issuer; no supplied upstream guarantee to subject','estate_id':r['estate_id'],'evidence_refs':r['evidence_refs']})
        if r['seniority']=='unknown': issues.append(r['instrument_id']+': legal priority unresolved')
    result={'financial_context':{k:f[k] for k in ('currency','unit','period','accounting_basis','consolidation_scope')},'credit_metrics':metrics,'cash_flow':cash_flow,
        'structural_risks':structural,'risk_observations':deepcopy(doc.get('risk_observations',[])),'ebitda_adjustments':deepcopy(doc.get('ebitda_adjustments',[])),
        'evidence_reconciliation':{'ebitda_adjustments':adjustment_reconciliation,'debt_inventory':debt_reconciliation},
        'rating_assigned':False,'credit_decision':'not-made','legal_priority':'supplied-assertions-only'}
    return done(doc,SKILL,result,issues,[{'metric':'credit_metrics','formula':'source-bound additive event reconciliation; exact included principal plus carrying-value bridge equals reported gross debt; reconciled debt / positive EBITDA',
        'adjustment_event_ids':[event.get('economic_event_id') for event in doc.get('ebitda_adjustment_events',[])],
        'included_instrument_ids':debt_reconciliation['included_instrument_ids'],'bridge_ids':[row['bridge_id'] for row in (doc.get('debt_reconciliation') or {}).get('bridge',[])],
        'evidence_refs':deepcopy(doc['evidence_refs'])}])
