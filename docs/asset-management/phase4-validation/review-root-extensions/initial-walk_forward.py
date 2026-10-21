"""Bounded purged walk-forward evidence and cost-path review; no backtest engine."""
from datetime import timedelta
from decimal import Decimal
from foundation_contract import D, exact, finish, require_sources, text, date_value, validate_actual_date, validate_common

EXTENSION='walk-forward'


def records(doc,key):
    rows=doc.get(key)
    if not isinstance(rows,list) or not rows or len(rows)>10000 or any(not isinstance(r,dict) for r in rows): raise ValueError(key+' requires bounded nonempty records')
    ids=[r.get('id') for r in rows]
    if any(not text(v) for v in ids) or len(set(ids))!=len(ids): raise ValueError(key+' requires unique nonempty IDs')
    for r in rows: require_sources(doc,[r.get('source_ref')])
    return rows


def ids(value,label):
    if not isinstance(value,list) or not value or any(not text(x) for x in value) or len(set(value))!=len(value): raise ValueError(label+' requires unique nonempty IDs')
    return set(value)


@exact
def compute(doc):
    errors=validate_common(doc)
    if errors: raise ValueError('; '.join(errors))
    if doc.get('extension')!=EXTENSION: raise ValueError('unsupported systematic research extension')
    require_sources(doc,[doc.get('protocol_source_ref'),doc.get('universe_source_ref')])
    for key in ('strategy_version','protocol_version','data_snapshot','execution_model_version'):
        if not text(doc.get(key)) or doc[key].lower() in {'latest','unknown'}: raise ValueError('pinned '+key+' required')
    budget=doc.get('predeclared_trial_limit');embargo=doc.get('embargo_days')
    if any(isinstance(v,bool) or not isinstance(v,int) or v<0 for v in (budget,embargo)) or budget<1: raise ValueError('positive trial limit and nonnegative integer embargo required')
    trials=ids(doc.get('trials_considered'),'trials_considered')
    if doc.get('selected_trial_id') not in trials: raise ValueError('selected trial is absent from recorded search inventory')
    issues=[]
    if len(trials)>budget: issues.append('Actual trial inventory exceeds the predeclared search budget')
    if doc.get('universe_inventory_complete') is not True: issues.append('Historical eligible universe inventory remains unverified')
    universe={r['id']:r for r in records(doc,'universe')}
    for row in universe.values():
        date_value(row['eligible_from'])
        if row.get('eligible_to') is not None and date_value(row['eligible_to'])<date_value(row['eligible_from']): raise ValueError('reversed historical universe interval')
    folds=records(doc,'folds');samples={r['id']:r for r in records(doc,'samples')}
    foldids={r['id'] for r in folds}
    if any(s.get('fold_id') not in foldids or s.get('segment') not in {'train','test'} for s in samples.values()): raise ValueError('sample references unknown fold or segment')
    used_test_events=set();test_intervals=[];fold_results=[];all_net=[];all_gross=[]
    for fold in sorted(folds,key=lambda r:r['test_start']):
        start,end=date_value(fold['test_start']),date_value(fold['test_end'])
        if start>end: raise ValueError('reversed test fold')
        validate_actual_date(doc,fold['test_end'],fold['source_ref'])
        if any(start<=b and end>=a for a,b in test_intervals): raise ValueError('test fold windows overlap')
        test_intervals.append((start,end))
        train_ids=ids(fold.get('train_ids'),'train_ids');test_ids=ids(fold.get('test_ids'),'test_ids')
        if train_ids & test_ids or not (train_ids|test_ids)<=set(samples): raise ValueError('train/test identity overlap or missing sample')
        actual={s['id'] for s in samples.values() if s['fold_id']==fold['id']}
        if train_ids|test_ids!=actual: raise ValueError('fold manifest differs from supplied sample population')
        local=[];path=[];growth=Decimal(1);gross_growth=Decimal(1);last_end=None
        training_events=set()
        for sid in train_ids:
            sample=samples[sid]
            if sample['segment']!='train': raise ValueError('training manifest includes a test sample')
            if not text(sample.get('event_id')): raise ValueError('source-bound economic event identity required')
            if sample['event_id'] in training_events: raise ValueError('duplicate training economic event')
            training_events.add(sample['event_id'])
        for sid in sorted(train_ids|test_ids,key=lambda x:samples[x]['observed_on']):
            sample=samples[sid]
            observed=validate_actual_date(doc,sample['observed_on'],sample['source_ref'])
            available=validate_actual_date(doc,sample['features_available_on'],sample['source_ref'])
            label_end=validate_actual_date(doc,sample['label_end'],sample['source_ref'])
            if label_end<observed: raise ValueError('label horizon precedes observation')
            if available>observed: local.append('Feature lookahead: '+sid)
            if sample.get('data_snapshot')!=doc['data_snapshot']: raise ValueError('sample belongs to a different data snapshot')
            present=ids(sample.get('universe_ids'),'sample universe_ids')
            historical={k for k,u in universe.items() if date_value(u['eligible_from'])<=observed and (u.get('eligible_to') is None or observed<=date_value(u['eligible_to']))}
            if present!=historical: local.append('Historical universe coverage differs: '+sid)
            if sid in train_ids:
                if label_end+timedelta(days=embargo)>=start: local.append('Training label/embargo reaches test window: '+sid)
                continue
            if sample['segment']!='test' or not start<=observed<=label_end<=end: raise ValueError('test sample horizon differs from fold')
            event=sample.get('event_id')
            if not text(event) or event in used_test_events or event in training_events: raise ValueError('test economic event reused across samples/training')
            used_test_events.add(event)
            if last_end is not None and observed<=last_end: raise ValueError('overlapping test return horizons cannot be geometrically compounded')
            last_end=label_end
            if sample.get('return_unit')!='decimal' or sample.get('turnover_basis')!='one-way-notional-over-nav': raise ValueError('return/turnover units differ from supported method')
            gross,turnover,cost,borrow,funding=(D(sample[k]) for k in ('gross_return','turnover','cost_bps','borrow_cost_return','funding_cost_return'))
            if gross < -1 or min(turnover,cost,borrow,funding)<0: raise ValueError('invalid return or cost assumptions')
            drag=turnover*cost/10000+borrow+funding;net=gross-drag
            if net < -1: raise ValueError('net return below -100% outside supported unlevered path')
            growth*=1+net;gross_growth*=1+gross;all_net.append(net);all_gross.append(gross)
            path.append({'id':sid,'gross_return':str(gross),'cost_drag_return':str(drag),'net_return':str(net),'source_ref':sample['source_ref']})
        issues.extend(fold['id']+': '+s for s in local)
        fold_results.append({'id':fold['id'],'issues':local,'test_count':len(path),'path':path,
                             'gross_compounded_return':str(gross_growth-1) if not local else None,
                             'net_compounded_return':str(growth-1) if not local else None})
    ng=gg=Decimal(1)
    for n,g in zip(all_net,all_gross): ng*=1+n;gg*=1+g
    clean=not issues and not doc.get('unresolved_issues')
    results={'folds':fold_results,'out_of_sample_period_count':len(all_net),
             'gross_compounded_return':str(gg-1) if clean else None,'net_compounded_return':str(ng-1) if clean else None,
             'performance_claim_supported':False,'backtest_executed':False,'deployment_authorized':False,
             'probability_of_backtest_overfitting':None,'trial_inventory_count':len(trials)}
    return finish(doc,'systematic-investment-research-reviewer','purged-walk-forward-evidence-v1',results,issues,
                  ['Supplied strategy-level nonoverlapping simple-return observations only; no market simulation or discovery.',
                   'Day-grain feature/label availability and a declared embargo do not prove source truth, complete trial inventory or semantic train/test independence.',
                   'No PBO, deflated Sharpe, significance, capacity or causal performance claim is computed; specialized inference requires an independently validated engine.'])
