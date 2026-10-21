"""Reviewed native IR adapters. Executes only local validation/computation (MIT).

Every mapping validates actual producer/receiver contracts with detached originals.
Installed packages are separate dependencies, verified against their manifests.
"""
from __future__ import annotations
import copy, json, subprocess, sys, tempfile
from pathlib import Path
from analysis_contract import validate_base, evidence_gaps, require
from native_integrity import attach_source, canonical_hash

VERSION='1.2.0'

def assign_projection(target,field,value):
    current=target.get(field)
    empty=current is None or current==[] or current=={} or (field=='model_review' and current=={'state':'not-supplied','issues':[]})
    require(empty or canonical_hash(current)==canonical_hash(value),'conflicting populated receiver field: '+field+'; adjudicate before mapping')
    target[field]=copy.deepcopy(value)

def package(root,name):
    doc=json.loads((root/'catalog/investment-research-capabilities.json').read_text())
    entries=[r for r in doc['capabilities'] if r['name']==name and r['support_status']!='planned']
    require(len(entries)==1,'adapter method unavailable: '+name)
    p=(root/entries[0]['path']).resolve()
    require(p.is_relative_to(root.resolve()) and p.name==name,'unsafe installed package path')
    manifest=json.loads((p/'references/package-manifest.json').read_text())
    require(manifest.get('skill')==name,'package manifest identity mismatch')
    actual={str(child.relative_to(p)) for child in p.rglob('*') if child.is_file()
            and child!=p/'references/package-manifest.json' and '__pycache__' not in child.parts
            and child.name!='.DS_Store' and child.suffix!='.pyc'}
    require(actual==set(manifest['files']),'package file inventory differs from manifest: '+name)
    import hashlib
    for rel,digest in manifest['files'].items():
        child=(p/rel).resolve()
        require(child.is_relative_to(p) and child.is_file(),'package file missing/unsafe')
        require(hashlib.sha256(child.read_bytes()).hexdigest()==digest,'package manifest drift: '+name+'/'+rel)
    return p,canonical_hash(manifest)

def invoke(p,script,doc,original=None):
    with tempfile.TemporaryDirectory(prefix='ir-reviewed-native-') as tmp:
        path=Path(tmp)/'document.json';path.write_text(json.dumps(doc,allow_nan=False))
        args=[sys.executable,'-B',str(p/'scripts'/script),str(path)]
        if original is not None:
            source=Path(tmp)/'original.json';source.write_text(json.dumps(original,allow_nan=False));args+=['--input',str(source)]
        import os
        env={k:v for k,v in os.environ.items() if k not in {'PYTHONPATH','PYTHONHOME'}};env['PYTHONDONTWRITEBYTECODE']='1'
        r=subprocess.run(args,cwd=p,text=True,capture_output=True,env=env,timeout=60)
        require(r.returncode==0,'native '+p.name+'/'+script+' rejected handoff: '+(r.stdout+r.stderr)[:900])
        if script=='calculate_or_transform.py': return json.loads(r.stdout)

def context_match(a,b):
    for key in ('subject','as_of','knowledge_cutoff','use_on','purpose','audience','information_barrier','pre_event','event_time'):
        require(a.get(key)==b.get(key),'handoff context mismatch: '+key)
    def unit(d): return d.get('units',d.get('unit',d.get('model_input',{}).get('units')))
    def currency(d):return d.get('currency',d.get('model_input',{}).get('currency'))
    if currency(a) is not None and currency(b) is not None:require(currency(a)==currency(b),'handoff currency mismatch')
    if unit(a) is not None and unit(b) is not None:require(unit(a)==unit(b),'handoff units mismatch')
    for key in ('accounting_basis','consolidation_scope'):
        if key in a and key in b:require(a[key]==b[key],'handoff basis mismatch: '+key)

def merge_evidence(source,target):
    sources={s['source_id']:copy.deepcopy(s) for s in target['sources']}
    for s in source['sources']:
        if s['source_id'] in sources:require(canonical_hash(s)==canonical_hash(sources[s['source_id']]),'source ID/version collision')
        sources[s['source_id']]=copy.deepcopy(s)
    target['sources']=list(sources.values())
    refs={(r['source_id'],r['locator']):copy.deepcopy(r) for r in target['evidence_refs']+source['evidence_refs']}
    target['evidence_refs']=list(refs.values())

def event_quality_packet(source,result,target):
    """Project event mechanics without inventing publication coverage or time basis."""
    bridge=result['financial_bridge'];basis=source['financial_basis'];event=source['event']
    scope=target.get('review_scope',{})
    required={'sections','claim_evidence','arithmetic','contradictions','comparability','risks','disclosures'}
    require(required<=set(scope.get('required_checks',[])),'event QA requires all seven explicit review checks')
    require('event-bridge' in scope.get('required_sections',[]) and 'event-funding' in scope.get('required_risks',[]) and 'event-conditionality' in scope.get('required_disclosures',[]),'event QA requires explicit bridge, funding-risk and conditionality coverage')
    claims=[];checks=[];numeric_ids=[]
    for state in ('before','change','after'):
        period=source['baseline']['balance_date'] if state=='before' else event['effective_date']
        forecast=state!='before' and event['status']!='completed'
        for component in ('cash','debt','net_debt','shares'):
            cid='event-'+state+'-'+component;numeric_ids.append(cid)
            b={'currency':'not-applicable' if component=='shares' else basis['currency'],
               'units':basis['share_units'] if component=='shares' else basis['units'],
               'accounting_basis':basis['accounting_basis'],'consolidation_scope':basis['consolidation_scope'],
               'period_end':period,'measure':'share-count' if component=='shares' else component}
            claim={'claim_id':cid,'kind':'forecast' if forecast else 'fact','subject_id':source['subject']['id'],
                   'text':state+' '+component+' in supplied '+event['type']+' bridge; '+result['effect_basis']+'; share basis '+json.dumps(source['valuation_subject'],sort_keys=True),
                   'known_at':source['knowledge_cutoff'],'evidence_refs':copy.deepcopy(source['evidence_refs']),
                   'value':bridge[state][component],'basis':b}
            if forecast:claim['forecast']={'horizon':event['effective_date'],'assumptions':[event['scenario_label'],'Only supplied event terms applied to the dated baseline; interim flows and market reactions are not modeled.']}
            claims.append(claim)
        checks.append({'check_id':'event-'+state+'-net-debt','operation':'difference',
                       'operand_claim_ids':['event-'+state+'-debt','event-'+state+'-cash'],
                       'reported_claim_id':'event-'+state+'-net_debt','tolerance':0.000001})
    for cid,text,rationale in (
        ('event-funding-review','Review funding availability and cash feasibility under supplied event mechanics.','Supplied cash feasibility does not establish external financing access or complete cash-flow coverage.'),
        ('event-conditionality-review','Review event status '+event['status']+' and effect basis '+result['effect_basis']+'.','Agreement, announcement and supplied completion are distinct; no legal completion, accounting fair value or market-price conclusion is established.')):
        claims.append({'claim_id':cid,'kind':'judgment','subject_id':source['subject']['id'],'text':text,
                       'known_at':source['knowledge_cutoff'],'evidence_refs':copy.deepcopy(source['evidence_refs']),'rationale':rationale})
    require(set(numeric_ids)<=set(scope.get('required_claim_ids',[])),'event QA must explicitly request all twelve bridge claims')
    require({r['check_id'] for r in checks}<=set(scope.get('required_arithmetic_ids',[])),'event QA must explicitly request three net-debt identities')
    packet={'packet_id':'event-impact-'+event['event_id'],'sections':[{'section_id':'event-bridge','claim_ids':numeric_ids}],
            'claims':claims,'arithmetic_checks':checks,'contradictions':[],'comparability_groups':[],
            'risks':[{'risk_id':'event-funding','claim_ids':['event-funding-review']}],
            'disclosures':[{'disclosure_id':'event-conditionality','claim_ids':['event-conditionality-review']}]}
    assign_projection(target,'packet',packet)
    return target

def mapped(spec,source,output,target,selection):
    result=output['results'];mode=spec['mapping'];exclusions=[]
    if mode=='candidate_model':
        require(result.get('model_kind')==spec['receiver'],'candidate model kind differs from receiver')
        candidate=result.get('candidate_input')
        require(isinstance(candidate,dict) and canonical_hash(candidate)==result.get('candidate_input_hash'),'candidate model hash mismatch')
        # Equality was checked before issue/evidence inheritance. Mapping cannot
        # replace a populated model, or claim that preparing it ran its engine.
        context_match(candidate,target)
    elif mode=='event_quality_packet':
        target=event_quality_packet(source,result,target)
    elif mode=='forecast_rows':
        require(result.get('forecast_rows'),'producer has no supported forecast rows')
        assign_projection(target,'forecast_rows',result['forecast_rows'])
    elif mode=='maturities':
        require(result.get('instrument_inventory_complete') is True and target.get('maturity_inventory_complete') is True,'full inventory completeness must be explicitly supplied by both parties')
        currency=selection.get('currency');unit=selection.get('unit')
        require(currency==target.get('currency') and unit==target.get('unit'),'explicit selected currency/unit must match receiver')
        groups=[g for g in result['currency_unit_groups'] if g['currency']==currency and g['unit']==unit]
        require(len(groups)==1,'selected maturity group unavailable')
        group=groups[0]
        require(group['principal_complete'] and group['maturity_complete'],'incomplete maturity inventory cannot be mapped as complete')
        require(all(r['date']>=target['as_of'] or r['amount']==0 for r in group['maturities']),'unresolved past-due principal requires separate adjudication')
        projection=[{'id':'maturity-'+r['instrument_id'],'instrument_id':r['instrument_id'],'date':r['date'],'amount':r['amount'],'currency':currency,'unit':unit,'evidence_refs':copy.deepcopy(r['evidence_refs'])} for r in group['maturities'] if target['as_of']<=r['date']<=target['horizon_end']]
        assign_projection(target,'maturities',projection)
        exclusions=[{'instrument_id':r['instrument_id'],'date':r['date'],'amount':r['amount'],'reason':'outside explicitly requested horizon'} for r in group['maturities'] if not target['as_of']<=r['date']<=target['horizon_end']]
    elif mode=='reviewed_definitions':
        require(not output['unresolved_issues'],'unresolved governing terms cannot be promoted into covenant tests')
        require(result.get('document_inventory_complete') is True and result.get('governing_version') is not None,'governing document inventory must be explicitly complete')
        definitions=[]
        for row in result['effective_terms']:
            term=row['term'];value=term.get('value')
            if row['status']=='reviewed-explicit' and term.get('field')=='reviewed-covenant-test-definition' and isinstance(value,dict):
                require(value.get('instrument_id')==result['instrument_id'],'term definition instrument mismatch')
                require(value.get('document_id')==row['document_id'] and value.get('document_version')==row['document_version'],'term definition document/version mismatch')
                require(value.get('definition_reviewed') is True,'unreviewed covenant definition')
                definitions.append(copy.deepcopy(value))
        require(bool(definitions),'no explicit reviewed covenant definitions; clause interpretation unsupported')
        assign_projection(target,'tests',definitions)
    elif mode=='equity_valuation':
        require(result.get('equity_value') is not None,'producer has no equity valuation')
        require(source.get('valuation_subject')==target.get('valuation_subject') and bool(source.get('valuation_subject')),'valuation security/share-class mismatch')
        row={'method_id':spec['producer'],'equity_value':result['equity_value'],
             'currency':source['currency'],'units':source['units'],'valuation_date':source['as_of'],
             'accounting_basis':source['accounting_basis'],'consolidation_scope':source['consolidation_scope'],
             'share_basis':source['valuation_subject']['share_count_basis'],'diluted_shares':source['diluted_shares'],
             'valuation_subject':copy.deepcopy(source['valuation_subject']),
             'valuation_timing':source['valuation_timing'],
             'discount_origin':result['discount_origin'],
             'first_forecast_year':result['first_forecast_year'],
             'assumption_differences':copy.deepcopy(selection.get('assumption_differences',[])),
             'evidence_refs':copy.deepcopy(source['evidence_refs'])}
        require(all(r['method_id']!=row['method_id'] for r in target['methods']),'duplicate valuation method')
        target['methods'].append(row)
    elif mode=='model_review':
        require(source.get('mode')=='independent-review','legacy continuity result cannot imply independent model review')
        # The receiver distinguishes findings from clearance; exact state naming is
        # deliberately bounded and validated by its native intake.
        assign_projection(target,'model_review',{'state':'review-required' if output['unresolved_issues'] else 'native-reviewed','issues':copy.deepcopy(output['unresolved_issues'])})
    else:raise ValueError('unregistered adapter mapping')
    return target,exclusions

def review(payload,library_root):
    root=Path(library_root).resolve();canonical_hash(payload)
    require(isinstance(payload,dict),'handoff request must be an object')
    registry=json.loads((root/'catalog/investment-research-adapters.json').read_text())
    specs=[r for r in registry['adapters'] if r['id']==payload.get('adapter_id')]
    require(len(specs)==1,'unknown reviewed adapter')
    spec=specs[0];source=payload.get('producer_input');output=payload.get('producer_output');target=copy.deepcopy(payload.get('receiver_input'))
    validate_base(source);validate_base(target);context_match(source,target)
    require(isinstance(output,dict),'producer output required')
    producer,pin=package(root,spec['producer']);receiver,rpin=package(root,spec['receiver'])
    invoke(producer,'validate_input.py',source);invoke(producer,'validate_output.py',output,source)
    require(not evidence_gaps(source) and output.get('results') is not None,'producer evidence ineligible; no mapped payload released')
    if spec['mapping']=='candidate_model':
        require(canonical_hash(target)==canonical_hash(output['results'].get('candidate_input')),'receiver must equal the exact proposed candidate input; conflicting model requires adjudication')
    merge_evidence(source,target)
    target['unresolved_issues']=sorted(set(target.get('unresolved_issues',[])+output.get('unresolved_issues',[])))
    target,exclusions=mapped(spec,source,output,target,payload.get('selection',{}))
    validate_base(target);require(not evidence_gaps(target),'receiver evidence ineligible; no mapped payload released')
    invoke(receiver,'validate_input.py',target)
    result=invoke(receiver,'calculate_or_transform.py',target)
    invoke(receiver,'validate_output.py',result,target)
    import hashlib
    return attach_source({'schema_version':'ir-reviewed-handoff/1.0','adapter_id':spec['id'],'adapter_method_version':VERSION,
        'adapter_implementation_hash':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'mapping_exclusions':exclusions,
        'producer':spec['producer'],'receiver':spec['receiver'],'mapping_scope':spec['scope'],
        'producer_output_hash':canonical_hash(output),'producer_input_hash':canonical_hash(source),
        'registry_hash':canonical_hash(registry),'package_manifest_hashes':{'producer':pin,'receiver':rpin},
        'receiver_input':target,'receiver_output':result,'status':'validated-native-handoff',
        'unresolved_issues':copy.deepcopy(result.get('unresolved_issues',[])),
        'source_assurance':'supplied-not-authenticated','professional_acceptance':'not-established',
        'authority_granted':False,'action_taken':False,'approval':'not_requested','execution':'not_performed'},payload)
