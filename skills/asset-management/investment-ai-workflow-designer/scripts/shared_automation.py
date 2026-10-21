"""Paired operational observations and explicit capacity/cash economics."""
from decimal import Decimal
from design_support import Review, total, ratio, validate_with
METHOD='paired-workflow-automation-v1'


def evaluate(doc):
    r=Review(doc,METHOD);d=r.data
    cases=r.rows('cases','case_id');scenarios=r.rows('scenarios','scenario_id');controls=r.rows('controls','control_id')
    r.fields(d,('population','comparison_protocol','owner','currency','workflow_version'))
    r.flag(d,'paired_inventory_complete');r.flag(d,'measurement_protocol_reviewed')
    r.need(d.get('comparison_type')=='paired-same-cases','comparison','This method requires paired same-case observations')
    r.need(d.get('requested_mode') in {'assist','draft','deterministic-automation','autonomous-regulated-decision'},'mode','Unknown automation mode')
    pairs=[]
    for row in cases:
        r.need(row.get('workflow_version')==d.get('workflow_version') and row.get('population')==d.get('population'),'cohort','Observed pair differs from workflow/population',row)
        r.date(row,'observed_on')
        vals={k:r.num(row,k) for k in ('baseline_human_minutes','candidate_human_minutes','baseline_nonlabor_cost','candidate_nonlabor_cost','baseline_elapsed_seconds','candidate_elapsed_seconds')}
        r.need(row.get('currency')==d.get('currency'),'currency','Paired nonlabor costs require scope currency',row)
        for k in ('baseline_error','candidate_error'):
            r.need(isinstance(row.get(k),bool),'outcome','Both independently reviewed error labels must be known booleans',row)
        pairs.append(vals)
    measurement_valid=r.clear
    mean={k:ratio(total(x[k] for x in pairs),Decimal(len(pairs))) if measurement_valid else None for k in ('baseline_human_minutes','candidate_human_minutes','baseline_nonlabor_cost','candidate_nonlabor_cost','baseline_elapsed_seconds','candidate_elapsed_seconds')}
    saved=mean['baseline_human_minutes']-mean['candidate_human_minutes'] if measurement_valid else None
    errors={kind:ratio(Decimal(sum(x.get(kind+'_error') is True for x in cases)),Decimal(len(cases))) if measurement_valid else None for kind in ('baseline','candidate')}
    required={'human-review','privacy','permission-scope','failure-recovery','auditability','evaluation-quality'}
    r.need(required <= {x['control_id'] for x in controls},'control-coverage','Missing automation control categories')
    controls_ok=True
    for row in controls:
        r.fields(row,('owner','test','actual'))
        r.need(row.get('status') in {'passed','failed','not-run'},'control-status','Use passed/failed/not-run',row)
        if row.get('status')!='passed':
            controls_ok=False;r.add('control-open','Control is not passed: '+row['control_id'],row,'review' if row.get('status')=='failed' else 'gap')
    if d.get('requested_mode')=='autonomous-regulated-decision':
        controls_ok=False;r.add('authority-boundary','The package cannot recommend autonomous regulated decisions',severity='review')
    threshold=r.num(d,'maximum_candidate_error_rate',proportion=True)
    quality=errors['candidate'] is not None and threshold is not None and errors['candidate']<=threshold
    if measurement_valid and not quality:r.add('quality-break','Candidate error rate exceeds the supplied maximum',severity='review')
    results=[]
    for row in scenarios:
        before=len(r.findings);r.evidence(row)
        vals={k:r.num(row,k,proportion=k in {'eligible_fraction','cash_realization_fraction'}) for k in ('annual_volume','eligible_fraction','hourly_labor_cost','cash_realization_fraction','annual_fixed_cost','implementation_cost')}
        r.need(row.get('currency')==d.get('currency'),'currency','Scenario currency differs',row)
        valid=measurement_valid and all(v is not None for v in vals.values()) and not any(f['severity']=='gap' for f in r.findings[before:])
        volume=vals['annual_volume']*vals['eligible_fraction'] if valid else None
        hours=volume*saved/Decimal(60) if valid else None
        labor_value=volume*saved*vals['hourly_labor_cost']/Decimal(60) if valid else None
        nonlabor=volume*(mean['baseline_nonlabor_cost']-mean['candidate_nonlabor_cost']) if valid else None
        net=labor_value*vals['cash_realization_fraction']+nonlabor-vals['annual_fixed_cost'] if valid else None
        payback=vals['implementation_cost']/net*12 if net is not None and net>0 else None
        results.append({'scenario_id':row['scenario_id'],'eligible_annual_volume':volume,'capacity_hours':hours,'capacity_value':labor_value,'nonlabor_saving':nonlabor,'annual_cash_net':net,'simple_payback_months':payback,'projection_not_observed':True})
    return r.finish({'paired_case_count':len(cases),'observed_means':mean,'human_minutes_saved_per_case':saved,'observed_error_rates':errors,
                     'scenarios':results,'pilot_candidate':r.clear and controls_ok and quality and any(x['annual_cash_net'] is not None and x['annual_cash_net']>0 for x in results),
                     'causal_effect_established':False,'automation_authorized':False})


def validate(doc):return validate_with(evaluate,doc)
