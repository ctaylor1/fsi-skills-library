"""Bounded detection, coverage and labeled sample metrics; no assurance or SAR conversion."""
from __future__ import annotations
from decimal import Decimal, localcontext
from foundation_contract import require_valid, result, day
from monitoring_contract import T,B,I,D,L,exact,fraction,enum,validate_schema,resolve,raw,metric,threshold_compare,decimal_equal

SKILL='transaction-monitoring-effectiveness-reviewer'
OBJECT_TYPE='transaction_monitoring_effectiveness_review'
METHOD='source-bound-population-label-effectiveness-review/1.0'
OBJECTS={
 'scope':{'review_id':T,'scenario_id':T,'scenario_version':T,'engine_id':T,'engine_version':T,
  'population_id':T,'population_unit':enum('economic-event','transaction','account','customer'),
  'population_definition':T,'population_ids':L,'window_from':D,'window_to':D,'cohort':T,
  'expected_count':I,'received_count':I,'extract_complete':B,'reconciliation_reference':T,
  'data_available_through':D,'freshness_criterion':T,'freshness_met':B,
  'mapping_dataset_id':T,'identifier_namespace':T,'entity_mapping_ref':T,'entity_mapping_version':T,
  'ambiguous_link_count':I,'conflicting_link_count':I,'graph_reference':T,'graph_version':T,'identity_limitations':T},
 'selection':{'sample_ids':L,'sampling_method':T,'selection_frame_reference':T,'selection_limitations':T,
  'label_definition':T,'label_reference_domain':T,'label_reference_version':T,
  'label_acceptance_reference':T,'label_owner':T,'label_limitations':T,
  'independent_assessment':B,'operational_involvement':B,'conflict_review':B,'reporting_line_review':B,
  'independence_review_reference':T,'leakage_assessed':B,'leakage_free':B,'training_item_ids':L},
 'criteria':{'minimum_precision':fraction,'minimum_recall':fraction,'unit':enum('fraction'),
  'owner':T,'review_reference':T,'basis':T},
 'operations':{'scenario_id':T,'scenario_version':T,'population_id':T,'cohort':T,'window_from':D,'window_to':D,
  'completed_reviews':I,'analyst_minutes':exact,'total_cost':exact,'currency':lambda v:T(v) and len(v)==3,
  'cost_accounting':enum('gross','net'),'outcomes_reference':T,'cost_limitations':T}
}
COLLECTIONS={
 'observations':('observation_id',{'item_id':T,'scenario_id':T,'scenario_version':T,
  'engine_id':T,'engine_version':T,'population_id':T,'cohort':T,'event_on':D,'observed_on':D,
  'detected':B,'engine_observation_reference':T,'label':enum('positive','negative','unassessed'),
  'label_reference_domain':T,'label_reference_version':T,'label_record_reference':T,'label_reviewed':B}),
 'benchmark_references':('benchmark_reference_id',{'reference_domain':T,'reference_version':T,
  'context':T,'claim':T,'limitation':T}),
 'technology_requirements':('technology_requirement_id',{'kind':enum('engine','vendor','model','copilot','real-time','graph'),
  'profile_id':T,'profile_version':T,'requirement':T,'owner':T,'review_reference':T,
  'requirement_supported':B,'limitation':T})
}


def validate(doc):
    errors,_=validate_schema(doc,OBJECT_TYPE,OBJECTS,COLLECTIONS)
    if errors: return errors,[]
    d=doc['data']; s=d['scope']; sel=d['selection']
    if raw(s,'review_id') != doc['object_id']: errors.append('review_id must match native object scope')
    if day(raw(s,'window_from')) and day(raw(s,'window_to')) and day(raw(s,'window_from'))>day(raw(s,'window_to')):
        errors.append('population window ends before start')
    pop,sample=raw(s,'population_ids'),raw(sel,'sample_ids')
    if pop is not None and sample is not None and not set(sample).issubset(pop):
        errors.append('selected sample outside supplied population scope')
    item_ids=[raw(r,'item_id') for r in d['observations'] if raw(r,'item_id') is not None]
    if len(item_ids)!=len(set(item_ids)): errors.append('duplicate economic item identities cannot be double-counted')
    if pop is not None and not set(item_ids).issubset(pop): errors.append('observation outside supplied population scope')
    for row in d['observations']:
        for field in ['scenario_id','scenario_version','engine_id','engine_version','population_id','cohort']:
            a,b=raw(row,field),raw(s,field)
            if a is not None and b is not None and a!=b:
                errors.append('observation scope/version/cohort differs: '+field)
        when=day(raw(row,'event_on'))
        start,end=day(raw(s,'window_from')),day(raw(s,'window_to'))
        if when and start and end and not start<=when<=end: errors.append('observation event outside supplied window')
    return errors,[]


def compute(doc):
    require_valid(doc,validate)
    issues=[]; blockers=[]; unknown=[]; d=doc['data']
    s=resolve(doc,d['scope'],OBJECTS['scope'],'scope',issues)
    sel=resolve(doc,d['selection'],OBJECTS['selection'],'selection',issues)
    criteria=resolve(doc,d['criteria'],OBJECTS['criteria'],'criteria',issues)
    op=resolve(doc,d['operations'],OBJECTS['operations'],'operations',issues)
    scope_fields=[k for k in s if k not in {'graph_reference','graph_version','identity_limitations'}]
    scope_ok=all(s[k] is not None for k in scope_fields)
    pop=s['population_ids']; sample=sel['sample_ids']
    if not scope_ok: blockers.append('population, lineage, mapping, timing or extract scope is unsupported/unknown')
    if not pop or s['expected_count']!=len(pop or []) or s['received_count']!=len(pop or []):
        scope_ok=False; blockers.append('population expected/received/distinct identity counts do not reconcile')
    if s['extract_complete'] is not True or s['freshness_met'] is not True:
        scope_ok=False; blockers.append('extract completeness or supplied freshness criterion unmet/unknown')
    if s['ambiguous_link_count'] or s['conflicting_link_count']:
        scope_ok=False; blockers.append('entity mapping has unresolved ambiguous/conflicting links')
    cutoff=day(doc['knowledge_cutoff'])
    if day(s['window_to']) and day(s['window_to'])>cutoff:
        scope_ok=False; blockers.append('population window exceeds observable knowledge cutoff')
    if day(s['data_available_through']) and day(s['window_to']) and day(s['data_available_through'])<day(s['window_to']):
        scope_ok=False; blockers.append('data completeness does not cover population window end')
    if day(s['data_available_through']) and day(s['data_available_through'])>cutoff:
        scope_ok=False; blockers.append('data availability evidence is future relative to cutoff')
    independent=None
    fields=['independent_assessment','operational_involvement','conflict_review','reporting_line_review','independence_review_reference']
    if all(sel[k] is not None for k in fields):
        independent=sel['independent_assessment'] is True and sel['operational_involvement'] is False and sel['conflict_review'] is True and sel['reporting_line_review'] is True
    label_fields=['sampling_method','selection_frame_reference','label_definition','label_reference_domain',
        'label_reference_version','label_acceptance_reference','label_owner','label_limitations']
    label_method_ok=bool(sample) and all(sel[k] is not None for k in label_fields) and independent is True
    if sel['leakage_assessed'] is not True or sel['leakage_free'] is not True or sel['training_item_ids'] is None:
        label_method_ok=False; blockers.append('sample leakage assessment is missing or adverse')
    if sample and sel['training_item_ids'] is not None and set(sample)&set(sel['training_item_ids']):
        label_method_ok=False; blockers.append('evaluation sample overlaps training item identities')
    if not label_method_ok: blockers.append('accepted label definition, sample selection or independence evidence incomplete/adverse')
    observations=[]; seen=set(); known_engine={}; sample_counts={'true_positive':0,'false_positive':0,'false_negative':0,'true_negative':0,'unknown':0}
    for row in d['observations']:
        v=resolve(doc,row,COLLECTIONS['observations'][1],row['observation_id'],issues)
        reasons=[]; engine_ok=True
        for field in ['item_id','scenario_id','scenario_version','engine_id','engine_version','population_id','cohort','event_on','observed_on','detected','engine_observation_reference']:
            if v[field] is None: engine_ok=False; reasons.append('engine observation '+field+' unsupported/unknown')
        if day(v['observed_on']):
            receipts=[day(src['received_at']) for src in doc['sources'] if src['source_ref'] in row['observed_on']['source_refs']]
            if day(v['observed_on'])>min([cutoff,day(doc['as_of'])]+receipts):
                engine_ok=False; reasons.append('engine observation is after cutoff/assessment/receipt')
            if day(v['event_on']) and day(v['observed_on'])<day(v['event_on']):
                engine_ok=False; reasons.append('engine observation predates event')
        if v['item_id'] is not None: seen.add(v['item_id'])
        if engine_ok: known_engine[v['item_id']]=v['detected']
        label_ok=label_method_ok and engine_ok and v['label'] in {'positive','negative'} and v['label_reviewed'] is True and v['label_record_reference'] is not None and v['label_reference_domain']==sel['label_reference_domain'] and v['label_reference_version']==sel['label_reference_version']
        state=None
        if sample is not None and v['item_id'] in sample:
            if label_ok:
                state=('true_positive' if v['detected'] else 'false_negative') if v['label']=='positive' else ('false_positive' if v['detected'] else 'true_negative')
            else:
                state='unknown'; reasons.append('selected item label/engine/reference evidence is unknown or inadmissible')
            sample_counts[state]+=1
        issues.extend(row['observation_id']+': '+reason for reason in reasons)
        observations.append({'observation_id':row['observation_id'],'evidence_kind':'engine-observation-with-separate-reference-label',
            'supplied_evidence':v,'eligible_engine_observation':engine_ok,'eligible_reference_label':label_ok,
            'sample_state':state,'issues':reasons})
    missing_selected=None if sample is None else sorted(set(sample)-seen)
    if missing_selected:
        sample_counts['unknown']+=len(missing_selected); issues.append('selected items lack observations: '+', '.join(missing_selected))
    missing_population=None if pop is None else sorted(set(pop)-set(known_engine))
    detection_count=sum(1 for value in known_engine.values() if value is True)
    engine_counts={'observed_known':len(known_engine),'detected':detection_count,
        'not_detected':len(known_engine)-detection_count,'unknown_or_absent':None if pop is None else len(missing_population)}
    coverage=metric(len(known_engine),len(pop)) if scope_ok and pop else None
    detection=metric(detection_count,len(known_engine)) if known_engine else None
    tp,fp,fn=sample_counts['true_positive'],sample_counts['false_positive'],sample_counts['false_negative']
    sample_ok=scope_ok and label_method_ok and sample_counts['unknown']==0 and bool(sample)
    precision=metric(tp,tp+fp) if sample_ok else None
    recall=metric(tp,tp+fn) if sample_ok else None
    if precision is None: unknown.append('sample precision unavailable: incomplete/invalid labels, detection or no labeled detections')
    if recall is None: unknown.append('sample recall unavailable: incomplete/invalid labels, detection or no reference positives')
    criteria_ok=all(value is not None for value in criteria.values())
    comparison={'precision':threshold_compare(tp,tp+fp,criteria['minimum_precision']) if precision and criteria_ok else None,
        'recall':threshold_compare(tp,tp+fn,criteria['minimum_recall']) if recall and criteria_ok else None}
    if any(value is False for value in comparison.values()): issues.append('observed labeled sample metric below supplied institutional criterion')
    if not criteria_ok: unknown.append('criterion comparisons withheld: institution criteria or acceptance reference unknown')
    operational_scope=all(op[k] is not None for k in ['scenario_id','scenario_version','population_id','cohort','window_from','window_to']) and all(op[k]==s[k] for k in ['scenario_id','scenario_version','population_id','cohort','window_from','window_to'])
    operational_metrics={'minutes_per_completed_review':None,'cost_per_completed_review':None,'currency':op['currency'],'cost_accounting':op['cost_accounting']}
    operational_basis_ok=operational_scope and op['outcomes_reference'] is not None and bool(op['completed_reviews'])
    for name,field in [('minutes_per_completed_review','analyst_minutes'),('cost_per_completed_review','total_cost')]:
        measure_basis_ok=operational_basis_ok and op[field] is not None
        if field=='total_cost':
            measure_basis_ok=measure_basis_ok and op['currency'] is not None and op['cost_accounting'] is not None
        if measure_basis_ok:
            with localcontext() as ctx:
                ctx.prec=max(40,len(op[field])+len(str(op['completed_reviews']))+20)
                operational_metrics[name]={'total':op[field],'completed_reviews':op['completed_reviews'],
                    'decimal':format(Decimal(op[field])/Decimal(op['completed_reviews']),'.12f'),'display_rounding':'12 places, half-even'}
        else:
            unknown.append(name+': unmeasured, unsupported basis or window/cohort incomparable')
    technology=[]
    for row in d['technology_requirements']:
        v=resolve(doc,row,COLLECTIONS['technology_requirements'][1],row['technology_requirement_id'],issues)
        if any(value is None for value in v.values()) or v['requirement_supported'] is not True:
            blockers.append(row['technology_requirement_id']+': supplied technology/control requirement unresolved')
        technology.append({'technology_requirement_id':row['technology_requirement_id'],**v})
    benchmarks=[{'benchmark_reference_id':r['benchmark_reference_id'],'evidence_kind':'benchmark-reference',
        **resolve(doc,r,COLLECTIONS['benchmark_references'][1],r['benchmark_reference_id'],issues)} for r in d['benchmark_references']]
    blockers=list(dict.fromkeys(blockers)); issues.extend(blockers)
    if blockers:
        comparison={'precision':None,'recall':None}
    # Optional metric unknowns are retained separately; no fabricated effectiveness verdict.
    issues.extend(unknown)
    return result(doc,SKILL,METHOD,{'scope':s,'sample_selection_and_label_method':sel,
        'population_reconciliation_consistent':scope_ok,'supplied_independence_evidence_consistent':independent,
        'observations':observations,'observed_engine_counts':engine_counts,'observed_detection_fraction':detection,
        'population_engine_observation_coverage':coverage,'missing_population_observations':missing_population,
        'selected_sample_counts':sample_counts,'missing_selected_observations':missing_selected,
        'sample_precision':precision,'sample_recall':recall,'supplied_criteria':criteria,
        'within_supplied_criteria':comparison,'operational_evidence':op,'operational_scope_comparable':operational_scope,
        'operational_unit_measures':operational_metrics,'technology_control_requirements':technology,
        'benchmark_references':benchmarks,'material_blockers':blockers,'unknown_metrics':unknown,
        'population_statistical_inference':'not-performed','effectiveness_verdict':'not-issued',
        'identity_resolution':'not-performed','sar_conversion':'not-performed','assurance_opinion':'not-issued'},issues,
        ['Positive/negative labels mean the supplied accepted target reference, never guilt, innocence, SAR filing or criminal truth.',
         'Counts are observed evidence and precision/recall describe only the exact labeled sample; no probability inference is implemented.',
         'Alert volume, review speed and unit cost are operational observations, not detection effectiveness.',
         'Benchmarks are contextual references and are not pooled with engine observations or used as institutional thresholds.'],
        ['transaction-monitoring-scenario-designer','compliance-control-testing-assistant',
         'financial-crime-technology-controls-reviewer','model-validation-assistant','compliance-remediation-evidence-reviewer'])
