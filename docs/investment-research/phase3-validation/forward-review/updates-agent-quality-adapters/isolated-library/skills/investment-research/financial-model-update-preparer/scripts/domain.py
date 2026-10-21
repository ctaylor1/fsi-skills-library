"""Immutable, bounded JSON model proposals; no workbook or live-store access."""
from __future__ import annotations
import copy,re
from analysis_contract import validate_base,number,require,rows,unique,references,finish,evidence_gaps
from native_integrity import canonical_hash
from research_runtime import calendar_date,temporal,text,only

SKILL='financial-model-update-preparer'
KINDS={'three-statement-model-builder','dcf-modeler'}
DATES=('as_of','knowledge_cutoff','use_on')
BASIS=('subject','purpose','audience','information_barrier','currency','units','accounting_basis','consolidation_scope','issuer_type')
DRIVERS={'revenue_growth','gross_margin','opex_pct_revenue','depreciation_rate','capex_pct_revenue','dso','dio','dpo','other_current_assets_pct_revenue','other_current_liabilities_pct_revenue','tax_rate','interest_rate','debt_repayment','dividend_payout_ratio'}
INCOME={'revenue','cogs','opex','depreciation','interest_expense','tax','net_income'}
BALANCE={'cash','accounts_receivable','inventory','other_current_assets','ppe_net','other_assets','accounts_payable','other_current_liabilities','debt','other_liabilities','equity'}
FORECAST={'revenue','ebit','depreciation','capex','delta_nwc','tax_rate','nopat','ufcf','year','period_start','period_end'}
BRIDGE={'total_debt','cash_and_equivalents','minority_interest','preferred_equity','investments_associates'}
CONTROL_KEYS={'authority_granted','action_taken','approval','execution','model_approved','live_model_updated','source_input'}


def digest(value,label):
    require(isinstance(value,str) and re.fullmatch('[0-9a-f]{64}',value),label+' must be a lowercase SHA-256 digest')


def parts(path):
    require(isinstance(path,str) and path.startswith('/') and len(path)<=256,'patch path must be a bounded absolute JSON pointer')
    result=path[1:].split('/')
    require(all(x and not re.search(r'~(?![01])',x) for x in result),'invalid JSON pointer escape or empty component')
    decoded=[x.replace('~1','/').replace('~0','~') for x in result]
    require('/'+'/'.join(x.replace('~','~0').replace('/','~1') for x in decoded)==path,'noncanonical JSON pointer')
    return decoded


def access(root,tokens):
    parent=root
    for token in tokens:
        if isinstance(parent,list):
            require(re.fullmatch('0|[1-9][0-9]*',token) is not None,'array indices must be canonical nonnegative integers')
            require(int(token)<len(parent),'patch index outside existing model inventory');parent=parent[int(token)]
        else:
            require(isinstance(parent,dict) and token in parent,'patch points to missing model field');parent=parent[token]
    return parent


def set_existing(root,tokens,value):
    parent=access(root,tokens[:-1]);key=int(tokens[-1]) if isinstance(parent,list) else tokens[-1]
    parent[key]=copy.deepcopy(value)


def allowed(kind,t):
    if kind=='three-statement-model-builder':
        if t==['model_input','forecast_years']:return 'integer'
        if t==['model_input','historical','year']:return 'year'
        if len(t)==4 and t[:2]==['model_input','historical'] and ((t[2]=='income_statement' and t[3] in INCOME) or (t[2]=='balance_sheet' and t[3] in BALANCE)):return 'number'
        if len(t)==4 and t[:2]==['model_input','drivers'] and t[2] in DRIVERS and t[3] in {'value','source'}:return 'source' if t[3]=='source' else 'number'
        if len(t)==3 and t[:2]==['model_input','drivers'] and t[2] in DRIVERS:return 'number'
        if len(t)==4 and t[:2]==['model_input','scenarios'] and t[2] in {'base','upside','downside'} and t[3] in {'revenue_growth_delta','gross_margin_delta'}:return 'number'
    else:
        if len(t)==1 and t[0] in {'wacc','terminal_growth','diluted_shares'}:return 'number'
        if t==['discounting']:return 'discounting'
        if len(t)==2 and t[0]=='bridge' and t[1] in BRIDGE:return 'number'
        if len(t)==3 and t[0]=='forecast_rows' and re.fullmatch('0|[1-9][0-9]*',t[1]) and t[2] in FORECAST:
            return 'date' if t[2] in {'period_start','period_end'} else 'year' if t[2]=='year' else 'number'
    raise ValueError('patch path outside supported financial input allowlist')


def guard_value(value,kind):
    if kind=='number':number(value,'patch value')
    elif kind in {'integer','year'}:
        require(isinstance(value,int) and not isinstance(value,bool),'patch integer/year must be an integer')
        require((1<=value<=100) if kind=='integer' else (1900<=value<=9999),'patch integer/year outside supported range')
    elif kind=='source':require(text(value) and len(value)<=4096,'driver source must be bounded nonempty text')
    elif kind=='date':calendar_date(value)
    elif kind=='discounting':require(value in {'mid_year','end_year'},'discounting requires mid_year or end_year')


def no_controls(value):
    if isinstance(value,dict):
        require(not CONTROL_KEYS.intersection(value),'native model contains unsupported execution/control/source-embedding fields')
        for item in value.values():no_controls(item)
    elif isinstance(value,list):
        for item in value:no_controls(item)


def bounded_native(original,kind):
    """Restrict candidate content to the supported native input, never arbitrary annotations."""
    common='request_id purpose audience subject as_of use_on knowledge_cutoff information_barrier sources evidence_refs unresolved_issues currency units accounting_basis consolidation_scope issuer_type event_time pre_event schema_version diluted_shares'
    if kind=='three-statement-model-builder':
        only(original,common+' model_input fiscal_calendar','original native three-statement input')
        require(original.get('fiscal_calendar')=='calendar','native fiscal_calendar must be calendar')
        if 'diluted_shares' in original:number(original['diluted_shares'],'native diluted_shares')
        m=original.get('model_input');require(isinstance(m,dict),'native model_input required')
        only(m,'company ticker as_of config_version currency units forecast_years historical drivers scenarios company_id','native model_input')
        for k in ('company','ticker','config_version','company_id'):
            if k in m:require(text(m[k]) and len(m[k])<=512,'native '+k+' must be bounded text')
        historical=m.get('historical');require(isinstance(historical,dict),'native historical object required')
        only(historical,'year income_statement balance_sheet','native historical')
        for key,fields in (('income_statement',INCOME),('balance_sheet',BALANCE)):
            values=historical.get(key);require(isinstance(values,dict),'native historical '+key+' object required')
            only(values,' '.join(fields),'native historical '+key)
            for value in values.values():number(value,'native historical scalar')
        guard_value(historical.get('year'),'year');guard_value(m.get('forecast_years'),'integer')
        drivers=m.get('drivers');require(isinstance(drivers,dict),'native drivers object required');only(drivers,' '.join(DRIVERS),'native drivers')
        for driver in drivers.values():
            if isinstance(driver,dict):
                only(driver,'value source','native driver');number(driver.get('value'),'native driver value');guard_value(driver.get('source'),'source')
            else:number(driver,'native driver scalar')
        scenarios=m.get('scenarios',{});require(isinstance(scenarios,dict),'native scenarios object required');only(scenarios,'base upside downside','native scenarios')
        for scenario in scenarios.values():
            require(isinstance(scenario,dict),'native scenario object required');only(scenario,'revenue_growth_delta gross_margin_delta','native scenario')
            for value in scenario.values():number(value,'native scenario delta')
    else:
        only(original,common+' forecast_rows wacc terminal_growth discounting bridge valuation_subject valuation_timing','original native DCF input')
        forecasts=rows(original.get('forecast_rows'),'native forecast_rows',nonempty=True);require(len(forecasts)<=100,'native forecast inventory exceeds supported scope')
        for row in forecasts:
            require(isinstance(row,dict),'native forecast row object required');only(row,' '.join(FORECAST|{'currency','units','accounting_basis','consolidation_scope'}),'native forecast row')
            for key in FORECAST:
                guard_value(row.get(key),'date' if key in {'period_start','period_end'} else 'year' if key=='year' else 'number')
            for key in ('currency','units','accounting_basis','consolidation_scope'):require(row.get(key)==original.get(key),'native forecast row basis mismatch: '+key)
        bridge=original.get('bridge');require(isinstance(bridge,dict),'native bridge required');only(bridge,' '.join(BRIDGE),'native bridge')
        for value in bridge.values():number(value,'native bridge scalar')
        subject=original.get('valuation_subject');require(isinstance(subject,dict),'native valuation_subject required');only(subject,'security_id share_class share_count_basis','native valuation_subject')
        for key in ('security_id','share_class','share_count_basis'):require(text(subject.get(key)) and len(subject[key])<=512,'native valuation subject requires bounded '+key)
        for key in ('wacc','terminal_growth','diluted_shares'):number(original.get(key),'native '+key)
        guard_value(original.get('discounting'),'discounting')
        require(original.get('valuation_timing')=='annual-period-index','native valuation timing must be annual-period-index')
    for ref in original['evidence_refs']:only(ref,'source_id locator','native citation')


def transition(doc,original):
    tr=doc.get('context_transition');require(isinstance(tr,dict),'context_transition required')
    only(tr,'mode from to rationale evidence_refs','context_transition')
    require(tr.get('mode') in {'same-snapshot','advance-snapshot'},'explicit context transition mode required')
    require(tr.get('from')=={k:original[k] for k in DATES},'context transition from must match retained original')
    require(tr.get('to')=={k:doc[k] for k in DATES},'context transition to must match current request')
    require(text(tr.get('rationale')),'context transition rationale required')
    require(bool(tr.get('evidence_refs')),'context transition evidence required');references(doc,tr['evidence_refs'])
    changed=False
    for key in DATES:
        before,after=temporal(original[key]),temporal(doc[key])
        require(before[0]==after[0],'context transition cannot change temporal precision')
        require(after[1]>=before[1],'context transition cannot regress '+key)
        changed=changed or after[1]>before[1]
    require(changed == (tr['mode']=='advance-snapshot'),'transition mode must match actual date advancement')


def validate_document(doc):
    validate_base(doc)
    require(doc.get('schema_version')=='ir-phase3/1.0','Phase 3 schema_version required')
    only(doc,'request_id purpose audience subject as_of use_on knowledge_cutoff information_barrier sources evidence_refs unresolved_issues currency units accounting_basis consolidation_scope issuer_type event_time pre_event schema_version model_kind model_id base_version proposed_version original_model original_model_hash observed_current context_transition required_update_paths patches','model update input')
    require(doc.get('model_kind') in KINDS,'supported native model_kind required')
    for k in ('model_id','base_version','proposed_version'):require(text(doc.get(k)) and len(doc[k])<=256,k+' requires bounded nonempty text')
    require(doc['base_version']!=doc['proposed_version'],'proposed_version must differ from base_version')
    original=doc.get('original_model');validate_base(original);no_controls(original);bounded_native(original,doc['model_kind'])
    require(original.get('schema_version')=='ir-phase2/1.0','original must be a native Phase 2 model input')
    require(original.get('issuer_type')=='nonfinancial-corporate','only nonfinancial corporate native models supported')
    for key in BASIS:
        if key=='issuer_type' and key not in doc:continue
        require(doc.get(key)==original.get(key),'immutable model identity/basis/context mismatch: '+key)
    for k in ('currency','units','accounting_basis','consolidation_scope'):require(text(doc.get(k)),k+' required')
    for key in ('event_time','pre_event'):require(doc.get(key)==original.get(key),'event framing cannot be changed by a model update')
    digest(doc.get('original_model_hash'),'original_model_hash')
    require(doc['original_model_hash']==canonical_hash(original),'retained original hash mismatch')
    current=doc.get('observed_current');require(isinstance(current,dict),'observed_current required');only(current,'version input_hash','observed_current')
    digest(current.get('input_hash'),'observed_current.input_hash')
    require(current.get('version')==doc['base_version'] and current['input_hash']==doc['original_model_hash'],'observed current version/hash conflict; rebase for separate review')
    for ref in doc['evidence_refs']:only(ref,'source_id locator','current citation')
    for source in original['sources']:
        require(source in doc['sources'],'original source metadata/version/rights must be preserved exactly; use a distinct ID for new versions')
    require(set(canonical_hash(r) for r in original['evidence_refs'])<=set(canonical_hash(r) for r in doc['evidence_refs']),'original citations cannot be dropped')
    require({s['source_id'] for s in doc['sources']}=={r['source_id'] for r in doc['evidence_refs']},'every source in a staged candidate must have a permission-gated evidence reference')
    transition(doc,original)
    if not evidence_gaps(doc):
        require(not evidence_gaps(original),'retained original evidence was ineligible at its recorded context; rebase/adjudicate separately')
    patches=rows(doc.get('patches'),'patches',nonempty=True);unique(patches,'patch_id','patches');require(len(patches)<=2000,'patch inventory exceeds bounded scope')
    required=rows(doc.get('required_update_paths'),'required_update_paths',nonempty=True)
    require(all(isinstance(x,str) for x in required) and len(set(required))==len(required),'required_update_paths must be unique strings')
    paths=[]
    for patch in patches:
        only(patch,'patch_id path before_hash value rationale evidence_refs','patch')
        path=patch.get('path');tokens=parts(path);value_kind=allowed(doc['model_kind'],tokens)
        prior=access(original,tokens);require(not isinstance(prior,(dict,list)) and prior is not None,'only existing non-null scalar fields may be replaced')
        guard_value(prior,value_kind);require('value' in patch,'patch replacement value required');guard_value(patch['value'],value_kind)
        digest(patch.get('before_hash'),'patch before_hash');require(patch['before_hash']==canonical_hash(prior),'patch prior value hash conflict')
        require(canonical_hash(prior)!=canonical_hash(patch['value']),'no-op patches are not updates')
        require(text(patch.get('rationale')),'patch rationale required')
        require(bool(patch.get('evidence_refs')),'each patch requires evidence');references(doc,patch['evidence_refs'])
        for earlier in paths:require(path!=earlier and not path.startswith(earlier+'/') and not earlier.startswith(path+'/'),'duplicate or overlapping patch paths')
        paths.append(path)
    require(set(required)==set(paths),'declared required update coverage must equal patch inventory; no omitted or undeclared updates')
    if doc['model_kind']=='three-statement-model-builder':
        model=original.get('model_input');require(isinstance(model,dict),'native model_input required')
        require(model.get('company_id')==original['subject'].get('issuer_id',original['subject']['id']),'original native company identity mismatch')
        for key in ('currency','units','as_of'):require(model.get(key)==original.get(key),'original native model '+key+' mismatch')
    else:
        require(isinstance(original.get('forecast_rows'),list) and bool(original['forecast_rows']),'native forecast_rows required')
    return []


def compute(doc):
    validate_document(doc);original=doc['original_model'];candidate=copy.deepcopy(original);ledger=[]
    for patch in doc['patches']:
        tokens=parts(patch['path']);prior=access(original,tokens);set_existing(candidate,tokens,patch['value'])
        ledger.append({'patch_id':patch['patch_id'],'path':patch['path'],'before':copy.deepcopy(prior),'after':copy.deepcopy(patch['value']),'before_hash':canonical_hash(prior),'after_hash':canonical_hash(patch['value']),'rationale':patch['rationale'],'evidence_refs':copy.deepcopy(patch['evidence_refs'])})
    for key in DATES+('request_id','sources','evidence_refs'):candidate[key]=copy.deepcopy(doc[key])
    inherited=sorted(set(original.get('unresolved_issues',[])+doc.get('unresolved_issues',[])))
    candidate['unresolved_issues']=inherited
    if doc['model_kind']=='three-statement-model-builder':candidate['model_input']['as_of']=doc['as_of']
    validate_base(candidate)
    context_changes=[{'path':'/'+key,'before_hash':canonical_hash(original.get(key)),'after_hash':canonical_hash(candidate.get(key))} for key in DATES+('request_id','sources','evidence_refs','unresolved_issues') if original.get(key)!=candidate.get(key)]
    if doc['model_kind']=='three-statement-model-builder' and original['as_of']!=candidate['as_of']:context_changes.append({'path':'/model_input/as_of','before_hash':canonical_hash(original['as_of']),'after_hash':canonical_hash(candidate['as_of'])})
    results={'model_id':doc['model_id'],'model_kind':doc['model_kind'],'base_version':doc['base_version'],'proposed_version':doc['proposed_version'],'original_model_hash':doc['original_model_hash'],'observed_current':copy.deepcopy(doc['observed_current']),'candidate_input':candidate,'candidate_input_hash':canonical_hash(candidate),'patch_ledger':ledger,'context_transition':copy.deepcopy(doc['context_transition']),'generated_context_changes':context_changes,'required_update_paths':copy.deepcopy(doc['required_update_paths']),'coverage':{'requested':len(doc['required_update_paths']),'prepared':len(ledger),'scope':'Only the caller-declared update inventory; missing unrequested updates cannot be detected.'},'native_validation':'not-performed','review_requirements':['Execute the actual target native input validator, calculation and original-bound output validator.','Review period completeness, financial plausibility and source fidelity under institution controls.','Obtain separate authorization immediately before any live model change.'],'validation_scope':'Structural immutable-original, version/hash conflict, field allowlist, explicit context and supplied-evidence checks. Native model semantics and economic effects require the actual target model.','live_model_updated':False,'model_approved':False}
    return finish(doc,SKILL,results,issues=inherited,lineage=[{'formula':'candidate = deep copy(retained original) + disjoint explicit scalar replacements + declared current context/evidence; candidate_hash = canonical SHA-256(candidate)','original_model_hash':doc['original_model_hash'],'candidate_input_hash':results['candidate_input_hash']}])
