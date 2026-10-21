"""Risk-to-scenario controlled proposal; no activation, backtest or identity resolution."""
from __future__ import annotations
from decimal import Decimal
from foundation_contract import require_valid, result, day
from monitoring_contract import T,B,I,D,L,exact,enum,validate_schema,resolve,raw,decimal_equal

SKILL='transaction-monitoring-scenario-designer'
OBJECT_TYPE='transaction_monitoring_scenario_design'
METHOD='risk-lineage-logic-change-proposal/1.0'
OBJECTS={
 'scenario':{'scenario_id':T,'design_version':T,'risk_id':T,'risk_hypothesis':T,
  'typology':T,'target_behavior':T,'population_id':T,'population_unit':enum('economic-event','transaction','account','customer'),
  'eligibility_definition':T,'engine_id':T,'engine_version':T,'processing_mode':enum('batch','real-time','hybrid'),
  'logic_spec':T,'window_value':exact,'window_unit':enum('minutes','hours','days'),
  'entity_mapping_ref':T,'entity_mapping_version':T,'mapping_dataset_id':T,'identifier_namespace':T,
  'ambiguous_link_count':I,'conflicting_link_count':I,'mapping_method':T,'identity_limitations':T,
  'graph_reference':T,'graph_version':T,'currency':lambda v:T(v) and len(v)==3,
  'amount_accounting':enum('gross','net','not-used')},
 'evaluation':{'backtest_dataset_id':T,'backtest_from':D,'backtest_to':D,
  'holdout_dataset_id':T,'holdout_from':D,'holdout_to':D,'training_item_ids':L,'holdout_item_ids':L,
  'sampling_method':T,'label_definition':T,'label_reference':T,'label_limitations':T,
  'leakage_assessed':B,'holdout_independent':B,'bias_dimensions':L,'metric_definitions':L,
  'acceptance_criteria':T,'criteria_owner':T,'criteria_review_reference':T,'evaluation_limitations':T},
 'change':{'change_id':T,'prior_configuration_ref':T,'proposed_configuration_ref':T,
  'owner':T,'approver_role':T,'planned_start':D,'shadow_mode_plan':T,'reconciliation_gate':T,
  'rollback_trigger':T,'rollback_configuration_ref':T,'rollback_owner':T,'review_cadence':T}
}
COLLECTIONS={
 'parameters':('parameter_id',{'name':T,'value':exact,'unit':T,'currency':T,'rationale':T}),
 'data_requirements':('requirement_id',{'field':T,'source_system':T,'source_version':T,
  'lineage_reference':T,'transformation':T,'null_handling':T,'data_owner':T,
  'event_identity_rule':T,'reconciliation_definition':T,'expected_count':I,'loaded_count':I,
  'expected_total':exact,'loaded_total':exact,'currency':T,'amount_accounting':enum('gross','net','not-used'),
  'data_available_through':D,'freshness_criterion':T,'freshness_met':B}),
 'technology_requirements':('technology_requirement_id',{'kind':enum('engine','vendor','model','copilot','real-time','graph'),
  'profile_id':T,'profile_version':T,'requirement':T,'owner':T,
  'review_reference':T,'requirement_supported':B,'limitation':T}),
 'engine_observations':('engine_observation_id',{'engine_id':T,'engine_version':T,
  'scenario_id':T,'scenario_version':T,'observation':T,'observed_on':D,'population_id':T}),
 'benchmark_references':('benchmark_reference_id',{'reference_domain':T,'reference_version':T,
  'context':T,'claim':T,'limitation':T})
}


def validate(doc):
    errors,_=validate_schema(doc,OBJECT_TYPE,OBJECTS,COLLECTIONS)
    if errors: return errors,[]
    d=doc['data']; s=d['scenario']; e=d['evaluation']
    if raw(s,'scenario_id') != doc['object_id']:
        errors.append('scenario_id must match actual native object scope')
    for start,end in [('backtest_from','backtest_to'),('holdout_from','holdout_to')]:
        if day(raw(e,start)) and day(raw(e,end)) and day(raw(e,start))>day(raw(e,end)):
            errors.append('evaluation window ends before start')
    for name in ['parameters','data_requirements','technology_requirements']:
        if not d[name]: errors.append(name+': explicit nonempty proposal requirements required')
    for row in d['engine_observations']:
        for field,scope_field in [('engine_id','engine_id'),('engine_version','engine_version'),('scenario_id','scenario_id'),('scenario_version','design_version'),('population_id','population_id')]:
            a,b=raw(row,field),raw(s,scope_field)
            if a is not None and b is not None and a!=b:
                errors.append('engine observation scope/version differs from design')
    names=[raw(r,'name') for r in d['parameters'] if raw(r,'name') is not None]
    if len(names)!=len(set(names)): errors.append('duplicate parameter names')
    return errors,[]


def compute(doc):
    require_valid(doc,validate)
    issues=[]; blockers=[]; unknown_metrics=[]
    d=doc['data']
    s=resolve(doc,d['scenario'],OBJECTS['scenario'],'scenario',issues)
    e=resolve(doc,d['evaluation'],OBJECTS['evaluation'],'evaluation',issues)
    c=resolve(doc,d['change'],OBJECTS['change'],'change',issues)
    for label,values in [('scenario',s),('evaluation',e),('change',c)]:
        for field,value in values.items():
            if value is None: blockers.append(label+'.'+field+': unsupported or unknown design prerequisite')
    if s['window_value'] is not None and Decimal(s['window_value']) == 0:
        blockers.append('scenario window must be positive')
    if s['ambiguous_link_count'] or s['conflicting_link_count']:
        blockers.append('source-bound entity mapping retains ambiguous or conflicting links')
    if e['backtest_dataset_id'] is not None and e['backtest_dataset_id']==e['holdout_dataset_id']:
        blockers.append('backtest and untouched holdout datasets share identity')
    if all(day(e[k]) for k in ['backtest_from','backtest_to','holdout_from','holdout_to']) and max(day(e['backtest_from']),day(e['holdout_from'])) <= min(day(e['backtest_to']),day(e['holdout_to'])):
        blockers.append('backtest and holdout evaluation time windows overlap')
    if e['training_item_ids'] is not None and e['holdout_item_ids'] is not None and set(e['training_item_ids']) & set(e['holdout_item_ids']):
        blockers.append('training and holdout item identities overlap')
    if e['leakage_assessed'] is not True or e['holdout_independent'] is not True:
        blockers.append('holdout leakage and independence evidence incomplete or adverse')
    if not e['bias_dimensions'] or not e['metric_definitions']:
        blockers.append('explicit cohort/bias dimensions and measurable evaluation definitions required')
    for field in ['backtest_to','holdout_to']:
        if day(e[field]) and day(e[field])>day(doc['knowledge_cutoff']):
            blockers.append(field+': evaluation evidence window is beyond knowledge cutoff')
    requirements=[]
    for row in d['data_requirements']:
        v=resolve(doc,row,COLLECTIONS['data_requirements'][1],row['requirement_id'],issues)
        missing=[k for k,val in v.items() if val is None]
        # Quantities are readiness evidence only; unknown totals never become zero.
        quantity_fields={'expected_count','loaded_count','expected_total','loaded_total'}
        critical=[k for k in missing if k not in quantity_fields]
        if critical: blockers.append(row['requirement_id']+': incomplete lineage/data/freshness prerequisite: '+', '.join(critical))
        quantity_complete=not (set(missing)&quantity_fields)
        reconciled=None
        if quantity_complete:
            reconciled=v['expected_count']==v['loaded_count'] and decimal_equal(v['expected_total'],v['loaded_total'])
            if not reconciled: blockers.append(row['requirement_id']+': supplied population/amount reconciliation differs')
        else:
            unknown_metrics.append(row['requirement_id']+': population or amount reconciliation unmeasured')
            blockers.append(row['requirement_id']+': data reconciliation gate remains unassessed')
        if v['freshness_met'] is not True: blockers.append(row['requirement_id']+': freshness criterion is unassessed or not met')
        if day(v['data_available_through']) and day(v['data_available_through'])>day(doc['knowledge_cutoff']):
            blockers.append(row['requirement_id']+': data evidence is after cutoff')
        if v['currency']!=s['currency'] or v['amount_accounting']!=s['amount_accounting']:
            blockers.append(row['requirement_id']+': incompatible currency/accounting basis')
        requirements.append({'requirement_id':row['requirement_id'],'supplied_requirements':v,'reconciliation_consistent':reconciled})
    params=[]
    for row in d['parameters']:
        v=resolve(doc,row,COLLECTIONS['parameters'][1],row['parameter_id'],issues)
        if any(value is None for value in v.values()): blockers.append(row['parameter_id']+': parameter value/unit/rationale unknown')
        if v['unit']=='currency' and v['currency']!=s['currency']: blockers.append(row['parameter_id']+': parameter currency differs')
        params.append({'parameter_id':row['parameter_id'],**v})
    technology=[]
    for row in d['technology_requirements']:
        v=resolve(doc,row,COLLECTIONS['technology_requirements'][1],row['technology_requirement_id'],issues)
        if any(x is None for x in v.values()) or v['requirement_supported'] is not True:
            blockers.append(row['technology_requirement_id']+': supplied technology/control requirement unresolved')
        technology.append({'technology_requirement_id':row['technology_requirement_id'],**v})
    required_kinds={'engine'}
    if s['processing_mode'] in {'real-time','hybrid'}: required_kinds.add('real-time')
    kinds={v['kind'] for v in technology}
    if not required_kinds.issubset(kinds): blockers.append('engine or real-time control requirements absent for processing mode')
    observations=[]
    for row in d['engine_observations']:
        v=resolve(doc,row,COLLECTIONS['engine_observations'][1],row['engine_observation_id'],issues)
        if day(v['observed_on']) and day(v['observed_on'])>day(doc['knowledge_cutoff']):
            issues.append(row['engine_observation_id']+': observation future relative to cutoff')
            v['observation']=None
        observations.append({'engine_observation_id':row['engine_observation_id'],'evidence_kind':'engine-observation',**v})
    benchmarks=[{'benchmark_reference_id':r['benchmark_reference_id'],'evidence_kind':'benchmark-reference',
        **resolve(doc,r,COLLECTIONS['benchmark_references'][1],r['benchmark_reference_id'],issues)} for r in d['benchmark_references']]
    if c['prior_configuration_ref'] is not None and c['prior_configuration_ref']==c['proposed_configuration_ref']:
        blockers.append('proposed configuration must have a distinct controlled-change identity')
    blockers=list(dict.fromkeys(blockers)); issues.extend(blockers)
    config=None if blockers else {'proposal_only':True,'scenario':s,'parameters':params,
        'change_id':c['change_id'],'configuration_reference':c['proposed_configuration_ref'],'activation':'not-performed'}
    return result(doc,SKILL,METHOD,{'risk_to_scenario_design':s,'data_requirements':requirements,
        'parameter_proposal':params,'evaluation_plan':e,'controlled_change_proposal':c,
        'technology_control_requirements':technology,'engine_observations':observations,
        'benchmark_references':benchmarks,'material_blockers':blockers,'unknown_metrics':unknown_metrics,
        'proposal_prerequisites_consistent':not blockers,'proposed_engine_configuration':config,
        'backtest_executed':False,'holdout_executed':False,'identity_resolution':'not-performed',
        'risk_or_legal_approval':'not-issued','activation':'not-performed'},issues,
        ['Risk hypothesis, entity links and graph references are supplied assertions, not proven identity or crime.',
         'Reconciliation consistency does not authenticate extracts or demonstrate detection effectiveness.',
         'No threshold defaults, universal weights, approved legal profile or executable engine configuration is supplied.'],
        ['transaction-monitoring-effectiveness-reviewer','compliance-control-testing-assistant',
         'financial-crime-technology-controls-reviewer','model-validation-assistant'])
