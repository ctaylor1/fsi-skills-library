"""Provider-neutral component/interface design and measured nonfunctional fit."""
from design_support import Review, total, validate_with
METHOD='component-interface-requirements-v1'


def evaluate(doc):
    r=Review(doc,METHOD);d=r.data
    components=r.rows('components','component_id');interfaces=r.rows('interfaces','interface_id')
    requirements=r.rows('requirements','requirement_id');tests=r.rows('measurements','requirement_id')
    by={x['component_id']:x for x in components}; req={x['requirement_id']:x for x in requirements}
    r.fields(d,('business_outcome','owner','currency','cost_period','scope'));r.flag(d,'inventory_complete')
    costs=[]
    for row in components:
        r.fields(row,('responsibility','owner','technology_choice','alternative','tradeoff','failure_domain','data_classification','retention_rule','recovery_runbook'))
        r.need(row.get('currency')==d.get('currency') and row.get('cost_period')==d.get('cost_period'),'cost-basis','Component costs require a common currency and period',row)
        costs.append(r.num(row,'cost'))
    pairs=set()
    for row in interfaces:
        pair=(row.get('from_component'),row.get('to_component'),row.get('contract_version'))
        r.need(row.get('from_component') in by and row.get('to_component') in by,'endpoint','Unknown component endpoint',row)
        r.need(pair not in pairs,'duplicate-flow','Duplicate logical flow under another ID',row);pairs.add(pair)
        r.fields(row,('contract_version','payload_schema','purpose','authentication','authorization_scope','encryption','timeout','failure_route','trace_id'))
        r.need(row.get('delivery') in {'synchronous','at-least-once','at-most-once'},'delivery','Declared delivery semantics are required; exactly-once is not inferred',row)
        r.need(row.get('operation') in {'read','proposed-write'},'operation','Interface operation must be read/proposed-write',row)
        r.flag(row,'purpose_reviewed')
        attempts=r.num(row,'max_attempts',integer=True);r.need(attempts is not None and 1<=attempts<=10,'attempts','Max attempts must be 1..10',row)
        if row.get('operation')=='proposed-write':r.fields(row,('idempotency_key','approval_owner','receipt_check','recovery_plan'))
    observed={x['requirement_id']:x for x in tests};fit=[]
    r.need(set(observed)<=set(req),'measurement-binding','Unknown measured requirement')
    for rid,row in req.items():
        r.fields(row,('component_id','metric','unit','owner','workload_profile'))
        r.need(row['component_id'] in by,'requirement-component','Requirement refers to missing component',row)
        r.need(row.get('operator') in {'<=','>='},'operator','Requirement operator must be <= or >=',row)
        threshold=r.num(row,'threshold');measurement=observed.get(rid)
        value=None;valid=False
        if measurement:
            valid=r.need(all(measurement.get(k)==row.get(k) for k in ('component_id','metric','unit','workload_profile')),'measurement-scope','Measurement workload, unit, metric or component differs',measurement)
            valid &= bool(r.date(measurement,'observed_on'));value=r.num(measurement,'value')
        else:r.add('measurement-missing','No measured evidence for '+rid,row)
        valid=valid and r.scope_valid and value is not None and threshold is not None
        meets=(value<=threshold if row.get('operator')=='<=' else value>=threshold) if valid else None
        if meets is False:r.add('nfr-break','Measured requirement not met: '+rid,row,'review')
        fit.append({'requirement_id':rid,'observed':value if valid else None,'threshold':threshold,'unit':row.get('unit'),'meets':meets})
    if not r.clear:
        for row in fit:row.update(observed=None,meets=None)
    return r.finish({'components':components,'interfaces':interfaces,'requirement_fit':fit,
                     'supplied_period_cost':total(costs) if r.clear else None,'currency':d.get('currency'),'cost_period':d.get('cost_period'),
                     'deployment_authorized':False,'provider_conformance':'not_assessed'})


def validate(doc):return validate_with(evaluate,doc)
