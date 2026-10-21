"""Bounded supplied-evidence research; no source authentication or execution."""
from datetime import date, datetime, timezone
from copy import deepcopy
from decimal import Decimal
from fractions import Fraction
from statistics import median
from analysis_contract import validate_base, number, require, rows, unique, references, finish
from research_runtime import temporal, source_reasons

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
    if lineage is None: lineage=[{'operation':'Reported comparable-period credit ratios; current minus prior; spread delta from reconciled source-bound observations and instrument mapping, with observation chronology, economic as-of and supplied current-age policy','input_binding':'complete-original-input-hash','input_fields':sorted(k for k in doc if k not in ('sources','evidence_refs')),'output_fields':sorted(result),'evidence_refs':deepcopy(doc['evidence_refs'])}]
    return finish(doc,skill,result,issues=issues or [],lineage=lineage)

SKILL='issuer-credit-surveillance-reviewer'
def validate_document(doc):
    base(doc); require(doc.get('issuer_profile')=='nonfinancial-corporate','corporate EBITDA profile required')
    cutoff_kind,cutoff=temporal(doc['knowledge_cutoff'])
    cutoff_day=cutoff.date() if cutoff_kind=='timestamp' else cutoff
    for key in ('prior','current'):
        f=obj(doc.get(key),key); field_context(f,key); cited(doc,f,key)
        require(day(f['period']['end'],key+'.period.end')<=day(doc['as_of'],'as_of'),key+' reported financial period ends after as_of; forecasts/scenarios are unsupported')
        require(day(f['period']['end'],key+'.period.end')<=cutoff_day,key+' reported financial period ends after knowledge_cutoff date; forecasts/scenarios are unsupported')
        for k in ('ebitda','gross_debt','unrestricted_cash','interest_expense','mandatory_capex','available_committed_facilities','near_term_maturities'): amount(f,k,nullable=True,minimum=0 if k!='ebitda' else None)
        flag(f.get('maturity_inventory_complete'),'maturity_inventory_complete')
    require(doc['prior']['period']['end']<doc['current']['period']['end'],'prior period must precede current')
    require(doc['prior']['period']['fiscal_calendar_id']==doc['current']['period']['fiscal_calendar_id'],'fiscal calendar differs')
    durations=[(day(doc[k]['period']['end'],'period.end')-day(doc[k]['period']['start'],'period.start')).days for k in ('prior','current')]
    require(abs(durations[0]-durations[1])<=3,'period duration differs; no annual/interim mixing')
    for k in ('currency','unit','accounting_basis','consolidation_scope'): require(doc['prior'][k]==doc['current'][k],k+' mismatch')
    cfg=obj(doc.get('thresholds'),'thresholds')
    for k in ('leverage_increase_x','coverage_decline_x','spread_widening_bps'): amount(cfg,k,minimum=0)
    for r in rows(doc.get('events'),'events'):
        obj(r,'event'); require(r.get('kind') in ('rating-reported','covenant-document-change','operating-risk','liquidity-risk'),'unsupported event kind'); text(r.get('text'),'event.text'); cited(doc,r,'event')
    for key in ('prior_spread','current_spread'):
        r=doc.get(key)
        if r is not None:
            obj(r,key)
            for k in ('security_id','currency','basis'): text(r.get(k),key+'.'+k)
            amount(r,'spread_bps'); cited(doc,r,key)
            for k in ('observation_id','issuer_id'):
                if r.get(k) is not None: text(r[k],key+'.'+k)
            if r.get('observed_at') is not None: stamp(r['observed_at'],key+'.observed_at')
    # Missing evidence is a bounded coverage gap; malformed supplied fields are
    # input errors. Semantic disagreements are reconciled below, not assumed true.
    for inventory in ('spread_evidence','instrument_evidence'):
        for index,r in enumerate(rows(doc.get(inventory,[]),inventory)):
            label=inventory+'['+str(index)+']'; obj(r,label)
            for k in ('observation_id','role','security_id','issuer_id','currency','basis'):
                if k in r: text(r[k],label+'.'+k)
            if 'spread_bps' in r: amount(r,'spread_bps')
            if 'observed_at' in r: stamp(r['observed_at'],label+'.observed_at')
            for k in ('valid_from','valid_to'):
                if k in r: temporal(r[k])
            if 'evidence_ref' in r:
                ref=obj(r['evidence_ref'],label+'.evidence_ref')
                for k in ('source_id','source_version','locator'):
                    if k in ref: text(ref[k],label+'.evidence_ref.'+k)
    policy=doc.get('spread_freshness_policy')
    if policy is not None:
        obj(policy,'spread_freshness_policy')
        amount(policy,'max_current_age_hours',minimum=0)

MAPPING_SOURCE_KINDS={'market_data','filing','credit_document','issuer_release'}

def evidence_source(doc,record,label,allowed_kinds,reasons):
    """Reconcile an asserted evidence block with its registered supplied source."""
    ref=record.get('evidence_ref')
    if not isinstance(ref,dict) or not all(ref.get(k) for k in ('source_id','source_version','locator')):
        reasons.append(label+' source_id/source_version/locator evidence binding missing'); return None
    source=next((s for s in doc['sources'] if s['source_id']==ref['source_id']),None)
    if source is None:
        reasons.append(label+' evidence source is not registered'); return None
    if ref['source_version']!=source['version']: reasons.append(label+' evidence source version mismatch')
    # Exact registered block identity prevents a mutually copied invented locator
    # from satisfying reconciliation. Register a precise block as its own source.
    if ref['locator']!=source['locator']: reasons.append(label+' evidence locator differs from registered source block')
    if source['kind'] not in allowed_kinds: reasons.append(label+' evidence source kind is unsupported for this role')
    if (ref['source_id'],ref['locator']) not in {(r['source_id'],r['locator']) for r in doc['evidence_refs']}:
        reasons.append(label+' evidence source block is not declared for permission gating')
    for reason in source_reasons(source,doc): reasons.append(label+' evidence source: '+reason)
    if not {record.get('security_id'),record.get('issuer_id')}<=set(source['subject_ids']):
        reasons.append(label+' evidence source must explicitly cover security and issuer')
    return source

def reconcile_spreads(doc,prior,current,reasons):
    """Use typed supplied evidence, not matching free-standing quote assertions."""
    resolved=[]
    for label,row in (('prior_spread',prior),('current_spread',current)):
        matches=[r for r in doc.get('spread_evidence',[]) if row.get('observation_id') and r.get('observation_id')==row['observation_id']]
        if len(matches)!=1:
            reasons.append(label+' requires exactly one selected spread evidence observation_id'); continue
        record=matches[0]; resolved.append(record)
        if record.get('role')!='spread-observation': reasons.append(label+' evidence role must be spread-observation')
        for k in ('security_id','issuer_id','currency','basis'):
            if not record.get(k) or record.get(k)!=row.get(k): reasons.append(label+' asserted '+k+' differs from selected evidence')
        if 'spread_bps' not in record or Decimal(str(record['spread_bps']))!=Decimal(str(row['spread_bps'])):
            reasons.append(label+' asserted spread_bps differs from selected evidence')
        if not record.get('observed_at') or not row.get('observed_at') or stamp(record['observed_at'],'evidence.observed_at')!=stamp(row['observed_at'],label+'.observed_at'):
            reasons.append(label+' asserted observed_at differs from selected evidence')
        # An alternate ID cannot conceal multiple supplied observations for the
        # same economic quote key. Unrelated unused records are not selected.
        key=('security_id','currency','basis')
        if record.get('observed_at'):
            same=[r for r in doc.get('spread_evidence',[]) if all(r.get(k)==record.get(k) for k in key) and r.get('observed_at') and stamp(r['observed_at'],'evidence.observed_at')==stamp(record['observed_at'],'evidence.observed_at')]
            if len(same)!=1: reasons.append(label+' duplicate or conflicting economic spread evidence')
        source=evidence_source(doc,record,label,{'market_data'},reasons)
        ref=record.get('evidence_ref',{})
        if [(r['source_id'],r['locator']) for r in row['evidence_refs']]!=[(ref.get('source_id'),ref.get('locator'))]:
            reasons.append(label+' asserted citation differs from selected evidence source block')
        if source is not None and record.get('observed_at'):
            if 'T' not in source['known_at']:
                reasons.append(label+' evidence source known_at lacks timestamp precision')
            elif stamp(source['known_at'],'source.known_at')<stamp(record['observed_at'],'evidence.observed_at'):
                reasons.append(label+' evidence source known_at precedes observation')
        issuer=doc['subject'].get('issuer_id') if doc['subject']['type']=='security' else doc['subject']['id']
        if record.get('issuer_id')!=issuer: reasons.append(label+' evidence issuer differs from requested subject')
        if doc['subject']['type']=='security' and record.get('security_id')!=doc['subject']['id']:
            reasons.append(label+' evidence security differs from requested security subject')
    if len(resolved)!=2: return None,None
    if resolved[0].get('observation_id')==resolved[1].get('observation_id'):
        reasons.append('prior and current require distinct selected observation_id values')
    security=resolved[1].get('security_id')
    mappings=[r for r in doc.get('instrument_evidence',[]) if security and r.get('security_id')==security]
    if len(mappings)!=1:
        reasons.append('selected security requires exactly one instrument evidence mapping'); return resolved,None
    mapping=mappings[0]
    if mapping.get('role')!='security-issuer-mapping': reasons.append('instrument evidence role must be security-issuer-mapping')
    evidence_source(doc,mapping,'instrument mapping',MAPPING_SOURCE_KINDS,reasons)
    for row in resolved:
        for k in ('security_id','issuer_id','currency'):
            if not mapping.get(k) or mapping.get(k)!=row.get(k): reasons.append('instrument mapping '+k+' differs from selected spread evidence')
        for field in ('valid_from','valid_to'):
            if not mapping.get(field):
                reasons.append('instrument mapping '+field+' missing'); continue
            if not row.get('observed_at'): continue
            kind,bound=temporal(mapping[field]); observed=stamp(row['observed_at'],'evidence.observed_at').astimezone(timezone.utc)
            instant=observed.date() if kind=='date' else observed
            if (field=='valid_from' and instant<bound) or (field=='valid_to' and instant>bound):
                reasons.append('instrument mapping '+field+' does not cover each selected observation')
    return resolved,mapping

def spread_change(doc,issues):
    """A source's known_at is not a market observation time or an age default."""
    prior,current=doc.get('prior_spread'),doc.get('current_spread')
    if not prior and not current: return None,{'status':'not-requested','observations':[],'instrument_mapping':None}
    reasons=[]
    resolved,mapping=None,None
    if not prior or not current:
        reasons.append('baseline missing')
    elif not all(prior[k]==current[k] for k in ('security_id','currency','basis')):
        reasons.append('security/currency/basis incomparable')
    else:
        resolved,mapping=reconcile_spreads(doc,prior,current,reasons)
        if prior.get('observed_at') is None or current.get('observed_at') is None:
            reasons.append('observed_at missing; source known_at cannot substitute')
        policy=doc.get('spread_freshness_policy')
        if policy is None: reasons.append('explicit spread_freshness_policy missing')
        if prior.get('observed_at') is not None and current.get('observed_at') is not None:
            a=stamp(prior['observed_at'],'prior_spread.observed_at').astimezone(timezone.utc)
            b=stamp(current['observed_at'],'current_spread.observed_at').astimezone(timezone.utc)
            cutoff_kind,cutoff=temporal(doc['knowledge_cutoff'])
            as_of=day(doc['as_of'],'as_of')
            if a>=b: reasons.append('prior observation must precede current observation')
            if cutoff_kind!='timestamp': reasons.append('knowledge_cutoff lacks timestamp precision')
            elif a>cutoff or b>cutoff: reasons.append('observation after knowledge_cutoff')
            if a.date()>as_of or b.date()>as_of: reasons.append('observation after economic as_of (UTC date)')
            sources={source['source_id']:source for source in doc['sources']}
            for key,row,observed in (('prior_spread',prior,a),('current_spread',current,b)):
                for ref in row['evidence_refs']:
                    source=sources[ref['source_id']]
                    if 'T' not in source['known_at']:
                        reasons.append(key+' cited source known_at lacks timestamp precision')
                    elif stamp(source['known_at'],'source.known_at').astimezone(timezone.utc)<observed:
                        reasons.append(key+' cited source known_at precedes observation')
            # Only the current observation is subject to the current-age policy.
            # The intentionally historical baseline retains its original timestamp.
            if policy is not None and cutoff_kind=='timestamp' and (cutoff-b).total_seconds()/3600>policy['max_current_age_hours']:
                reasons.append('current observation exceeds supplied maximum age')
    if reasons:
        issues.append('spread change withheld: '+'; '.join(dict.fromkeys(reasons)))
        return None,{'status':'withheld','observations':[],'instrument_mapping':None}
    delta=Fraction(str(resolved[1]['spread_bps']))-Fraction(str(resolved[0]['spread_bps']))
    value=delta.numerator if delta.denominator==1 else float(delta)
    number(value,'reconciled spread difference')
    return value,{'status':'reconciled-supplied-evidence','observations':deepcopy(resolved),'instrument_mapping':deepcopy(mapping)}
def compute(doc):
    validate_document(doc); issues=[]; out={}; alerts=[]
    for key in ('prior','current'):
        f=doc[key]; e=f['ebitda']; interest=f['interest_expense']; cash=f['unrestricted_cash']; debt=f['gross_debt']; facilities=f['available_committed_facilities']; maturities=f['near_term_maturities']
        out[key]={'gross_leverage_x':debt/e if e is not None and e>0 and debt is not None else None,'net_leverage_x':(debt-cash)/e if e is not None and e>0 and debt is not None and cash is not None else None,
            'interest_coverage_x':e/interest if e is not None and interest is not None and interest>0 else None,
            'fixed_charge_proxy_x':(e-f['mandatory_capex'])/interest if e is not None and f['mandatory_capex'] is not None and interest is not None and interest>0 else None,
            'liquidity_to_known_maturity_x':(cash+facilities)/maturities if cash is not None and facilities is not None and maturities is not None and maturities>0 and f['maturity_inventory_complete'] else None}
        if any(v is None for v in out[key].values()): issues.append(key+': dependent metrics withheld for missing/nonpositive values or incomplete maturities')
    changes={k:out['current'][k]-out['prior'][k] if out['current'][k] is not None and out['prior'][k] is not None else None for k in out['current']}
    if changes['net_leverage_x'] is not None and changes['net_leverage_x']>=doc['thresholds']['leverage_increase_x']: alerts.append('net leverage increased beyond supplied threshold')
    if changes['interest_coverage_x'] is not None and -changes['interest_coverage_x']>=doc['thresholds']['coverage_decline_x']: alerts.append('interest coverage declined beyond supplied threshold')
    spread,reconciliation=spread_change(doc,issues)
    if spread is not None and spread>=doc['thresholds']['spread_widening_bps']: alerts.append('spread widened beyond supplied threshold')
    return done(doc,SKILL,{'period_metrics':out,'metric_changes':changes,'spread_change_bps':spread,'spread_reconciliation':reconciliation,'alerts':alerts,'reported_events':deepcopy(doc['events']),
        'rating_action':'reported-only','position_action':'none','thesis_action':'unchanged','dscr_calculated':False,'coverage_limit':'fixed-charge EBITDA proxy is not a contractual debt-service ratio'},issues)
