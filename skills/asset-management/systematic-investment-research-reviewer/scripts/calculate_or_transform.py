#!/usr/bin/env python3
"""Review supplied temporal experiment controls and cost arithmetic, not strategy merit."""
from foundation_contract import D, date_value, exact, finish, source_issues, validate_common, cli_compute, validate_referenced_sources, validate_actual_date

@exact
def compute(doc):
    if isinstance(doc,dict) and "extension" in doc:
        from walk_forward import compute as compute_extension
        return compute_extension(doc)
    errors=validate_common(doc)
    if not errors:
        referenced_issues=validate_referenced_sources(doc)
        if 'source withheld for audience restriction' in referenced_issues:
            raise ValueError('request withheld for audience restriction')
        errors.extend(x for x in referenced_issues if "observation source as-of exceeds review date" in x)
    if errors: raise ValueError('; '.join(errors))
    issues=[]; results=[]; seen=set()
    experiments=doc['experiments']
    if not isinstance(experiments,list) or not experiments: raise ValueError('experiments must be nonempty')
    for e in experiments:
        eid=e['experiment_id']
        if eid in seen: raise ValueError('duplicate experiment_id')
        seen.add(eid); gaps=source_issues(doc,e.get('source_ref'))
        dates={k:date_value(e[k]) for k in ('train_start','train_end','train_label_end','validation_start','validation_end','test_start','test_end')}
        if not gaps:
            for field in dates: validate_actual_date(doc,e[field],e['source_ref'])
        gap=e['required_gap_days']
        if isinstance(gap,bool) or not isinstance(gap,int) or gap<0: raise ValueError('required_gap_days must be a nonnegative integer')
        checks=[]
        if not dates['train_start']<=dates['train_end']<=dates['train_label_end']: checks.append('training_or_label_order_invalid')
        if not dates['validation_start']<=dates['validation_end']<dates['test_start']<=dates['test_end']: checks.append('validation_test_overlap_or_order_invalid')
        if (dates['validation_start']-dates['train_label_end']).days<=gap: checks.append('train_label_overlap_or_gap_insufficient')
        if (dates['test_start']-dates['validation_end']).days<=gap: checks.append('validation_test_gap_insufficient')
        if dates['test_end']>date_value(doc['as_of']): checks.append('evaluation_period_after_review_date')
        trials=e['trials_considered']; uses=e['holdout_uses']; planned=e['predeclared_trial_limit']
        if any(isinstance(v,bool) or not isinstance(v,int) or v<1 for v in (trials,uses,planned)): raise ValueError('trial/holdout counts must be positive integers')
        if trials>planned: checks.append('trial_budget_exceeded_overfit_risk')
        if uses>1: checks.append('holdout_reused_selection_risk')
        if e.get('survivorship_control_reviewed') is not True: checks.append('survivorship_control_unverified')
        if not e['feature_availability']: checks.append('feature_availability_missing')
        for f in e['feature_availability']:
            fg=source_issues(doc,f.get('source_ref'));gaps.extend(fg)
            if not fg:
                validate_actual_date(doc,f['available_at'],f['source_ref'])
                validate_actual_date(doc,f['used_at'],f['source_ref'])
            if date_value(f['available_at'])>date_value(f['used_at']): checks.append('feature_lookahead:'+f['feature_id'])
        cost=None
        if e.get('turnover_definition')!='one_way_traded_notional_over_average_nav': gaps.append('unsupported turnover definition')
        elif e.get('turnover_fraction') is None or e.get('one_way_cost_bps') is None: gaps.append('cost assumptions unknown')
        elif not gaps:
            turnover=D(e['turnover_fraction']);unit_cost=D(e['one_way_cost_bps'])
            if turnover<0 or unit_cost<0: raise ValueError('turnover and costs must be nonnegative')
            drag=turnover*unit_cost
            cost={'period_start':e['test_start'],'period_end':e['test_end'],'turnover_fraction':str(turnover),'one_way_cost_bps':str(unit_cost),'implied_cost_drag_bps':str(drag),'reported_cost_drag_bps':e.get('reported_cost_drag_bps')}
            if e.get('reported_cost_drag_bps') is not None and D(e['reported_cost_drag_bps'])!=drag: checks.append('reported_cost_arithmetic_differs')
        issues.extend(eid+': '+g for g in gaps+checks)
        results.append({'experiment_id':eid,'source_ref':e.get('source_ref'),'control_findings':sorted(set(checks)),'data_gaps':gaps,'cost_check':cost,'performance_verified':False,'eligible_for_automatic_deployment':False})
    return finish(doc,'systematic-investment-research-reviewer','supplied-temporal-and-cost-review/1',{'experiments':results},issues,limitations=['No strategy backtest is run; no alpha, significance, capacity, live execution or future performance is established.','Daily boundaries and a supplied embargo are checked; intraday availability and overlapping labels need an approved engine.'])

if __name__=='__main__': cli_compute(compute)
