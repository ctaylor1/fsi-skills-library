"""Core option evidence, dependency waves and scoped migration control differences."""
from design_support import Review, ordered, total, validate_with
METHOD='insurance-core-option-migration-v1'


def evaluate(doc):
    r=Review(doc,METHOD);d=r.data
    requirements=r.rows('requirements','requirement_id');options=r.rows('options','option_id');batches=r.rows('batches','batch_id')
    controls=r.rows('reconciliations','control_id');gates=r.rows('gates','gate_id')
    r.fields(d,('currency','scope','owner','inventory_version'));r.flag(d,'inventory_complete')
    for row in requirements:
        r.fields(row,('description','owner'));r.need(isinstance(row.get('mandatory'),bool),'mandatory','Requirement mandatory must be explicit boolean',row)
    ids={x['requirement_id'] for x in requirements}; option_rows=[]
    for row in options:
        r.fields(row,('strategy','rationale','history_preservation','form_version_mapping','policy_identity_mapping','billing_claims_coexistence'))
        r.need(row.get('strategy') in {'retain','replatform','refactor','replace'},'strategy','Unsupported core option strategy',row)
        fits=r.rows('fits','requirement_id',row)
        r.need({x['requirement_id'] for x in fits}==ids,'fit-coverage','Every requirement needs exactly one option assessment',row)
        for fit in fits:
            r.need(fit.get('disposition') in {'met','not-met','unknown'},'fit','Fit must be met/not-met/unknown',fit)
            r.fields(fit,('rationale',))
            if fit.get('disposition')=='unknown':r.add('fit-unknown','Option fit is unresolved',fit)
        r.flag(row,'cost_inventory_complete');r.fields(row,('cost_horizon',))
        costs=r.rows('costs','cost_id',row)
        amounts=[]
        for cost in costs:
            r.need(cost.get('currency')==d.get('currency'),'currency','Option cost currency differs',cost)
            r.fields(cost,('period','basis'));amounts.append(r.num(cost,'amount'))
        mandatory={x['requirement_id'] for x in requirements if x.get('mandatory')}
        unmet=[x['requirement_id'] for x in fits if x['requirement_id'] in mandatory and x.get('disposition')=='not-met']
        if unmet:r.add('mandatory-not-met','Option fails mandatory needs: '+', '.join(unmet),row,'review')
        option_rows.append({'option_id':row['option_id'],'strategy':row.get('strategy'),'mandatory_not_met':unmet,'fits':fits,
                            'undiscounted_supplied_cost':total(amounts),'periods':[x.get('period') for x in costs]})
    r.need(len({x.get('cost_horizon') for x in options}) == 1, 'cost-horizon', 'Option costs must cover the same declared horizon')
    deps=[];by={x['batch_id']:x for x in batches};waves={x['batch_id']:r.num(x,'wave',integer=True) for x in batches}
    for row in batches:
        r.fields(row,('owner','scope','mapping_version','source_snapshot','target_snapshot','rollback_trigger','rollback_owner','rollback_data_plan'))
        r.flag(row,'rehearsal_evidence_reviewed');r.num(row,'wave',integer=True)
        for dep in r.strings(row,'depends_on'):
            deps.append((dep,row['batch_id']))
            r.need(dep in by and waves[dep] is not None and waves[row['batch_id']] is not None and waves[dep]<waves[row['batch_id']],'wave','Dependency must be in an earlier reviewed wave',row)
        r.need(isinstance(row.get('new_writes_after_cutover'),bool),'write-state','Explicit post-cutover write assumption required',row)
        if row.get('new_writes_after_cutover'):r.fields(row,('delta_recovery_evidence',))
    order=ordered(by,deps);r.need(order is not None,'dependency','Migration dependencies are dangling or cyclic')
    differences=[]
    for row in controls:
        batch=by.get(row.get('batch_id'))
        r.need(bool(batch),'control-batch','Reconciliation must identify a migration batch',row)
        if batch:
            r.need(all(row.get(k)==batch.get(k) for k in ('source_snapshot','target_snapshot','mapping_version','scope')),'snapshot','Control snapshot/mapping differs from batch',row)
        r.fields(row,('measure','unit','scope'))
        a=r.num(row,'source_value',signed=True);b=r.num(row,'target_value',signed=True);t=r.num(row,'tolerance')
        delta=b-a if a is not None and b is not None else None
        within=None if delta is None or t is None else abs(delta)<=t
        if within is False:r.add('reconciliation-break','Mapped source/target control difference exceeds supplied tolerance',row,'review')
        differences.append({'control_id':row['control_id'],'difference':delta,'within_tolerance':within,'unit':row.get('unit')})
    for bid in by:r.need(any(x.get('batch_id')==bid for x in controls),'control-missing','Every migration batch needs control evidence')
    for row in gates:
        r.fields(row,('owner','test','expected','actual'));r.date(row,'observed_on')
        r.need(row.get('status') in {'passed','failed','not-run'},'gate-status','Gate status must be passed/failed/not-run',row)
        if row.get('status')!='passed':r.add('gate-open','A migration test gate remains open',row,'review' if row.get('status')=='failed' else 'gap')
    required={'reconciliation','rollback','parallel-run','security','business-acceptance'}
    r.need(required <= {x['gate_id'] for x in gates},'gate-coverage','Required migration test categories are missing')
    if not r.clear:
        for row in option_rows:row['undiscounted_supplied_cost']=None
        for row in differences:row.update(difference=None,within_tolerance=None)
    return r.finish({'option_comparison':option_rows,'dependency_order':order,'migration_batches':batches,'reconciliation':differences,'gates':gates,
                     'selected_option':None,'cutover_authorized':False,'migration_executed':False})


def validate(doc):return validate_with(evaluate,doc)
