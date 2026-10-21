"""Bounded supplied-evidence research; no source authentication or execution."""
from datetime import date, datetime, timezone
from copy import deepcopy
from statistics import median
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
    if lineage is None: lineage=[{'operation':'Reported comparable-period credit ratios; current minus prior; matching spread observations subject to observation chronology, economic as-of and supplied current-age policy','input_binding':'complete-original-input-hash','input_fields':sorted(k for k in doc if k not in ('sources','evidence_refs')),'output_fields':sorted(result),'evidence_refs':deepcopy(doc['evidence_refs'])}]
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
            if r.get('observed_at') is not None: stamp(r['observed_at'],key+'.observed_at')
    policy=doc.get('spread_freshness_policy')
    if policy is not None:
        obj(policy,'spread_freshness_policy')
        amount(policy,'max_current_age_hours',minimum=0)

def spread_change(doc,issues):
    """A source's known_at is not a market observation time or an age default."""
    prior,current=doc.get('prior_spread'),doc.get('current_spread')
    if not prior and not current: return None
    reasons=[]
    if not prior or not current:
        reasons.append('baseline missing')
    elif not all(prior[k]==current[k] for k in ('security_id','currency','basis')):
        reasons.append('security/currency/basis incomparable')
    else:
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
        issues.append('spread change withheld: '+'; '.join(reasons))
        return None
    return current['spread_bps']-prior['spread_bps']
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
    spread=spread_change(doc,issues)
    if spread is not None and spread>=doc['thresholds']['spread_widening_bps']: alerts.append('spread widened beyond supplied threshold')
    return done(doc,SKILL,{'period_metrics':out,'metric_changes':changes,'spread_change_bps':spread,'alerts':alerts,'reported_events':deepcopy(doc['events']),
        'rating_action':'reported-only','position_action':'none','thesis_action':'unchanged','dscr_calculated':False,'coverage_limit':'fixed-charge EBITDA proxy is not a contractual debt-service ratio'},issues)
