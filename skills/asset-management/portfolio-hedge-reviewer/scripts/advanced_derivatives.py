"""Supplied nonlinear full-repricing review; deliberately no local pricing fallback."""
from foundation_contract import D,exact,finish,require_sources,text,validate_common
from specialist_contract import validate_specialist_common as validate_common
from specialist_contract import review_engine

EXTENSION='advanced-derivatives'

def rows(parent,key,identity):
    result=parent.get(key)
    if not isinstance(result,list) or not result or len(result)>10000 or any(not isinstance(x,dict) for x in result):raise ValueError(key+' requires bounded nonempty records')
    ids=[x.get(identity) for x in result]
    if any(not text(x) or '|' in x for x in ids) or len(set(ids))!=len(ids):raise ValueError(key+' requires unique separator-free identities')
    return result

@exact
def compute(doc):
    errors=validate_common(doc)
    if errors:raise ValueError('; '.join(errors))
    if doc.get('extension')!=EXTENSION or 'mode' in doc:raise ValueError('explicit advanced-derivatives extension required')
    request=doc.get('engine_request')
    if not isinstance(request,dict) or not isinstance(request.get('input'),dict):raise ValueError('engine request with detached input required')
    native=request['input']
    if native.get('valuation_method')!='full-repricing' or native.get('cost_basis')!='excludes-transaction-cost':raise ValueError('full repricing excluding transaction costs must be explicit')
    if native.get('portfolio_id')!=doc['object_id']:raise ValueError('engine portfolio differs from review object')
    for field in ('market_data_snapshot','curve_snapshot','volatility_snapshot','calendar_version','valuation_adjustments'):
        if not text(native.get(field)):raise ValueError(field+' requires pinned supplied evidence')
    limitations=native.get('model_limitations')
    if not isinstance(limitations,list) or not limitations or any(not text(x) for x in limitations):raise ValueError('explicit model limitations required')
    instruments=rows(native,'instruments','instrument_id');books=rows(native,'books','book_id');scenarios=rows(native,'scenarios','scenario_id');measures=rows(native,'measures','measure_id');costs=rows(native,'candidate_costs','book_id')
    instrument_ids={x['instrument_id'] for x in instruments}
    for instrument in instruments:
        require_sources(doc,[instrument.get('source_ref')])
        if not text(instrument.get('product_type')) or not isinstance(instrument.get('terms'),dict) or not instrument['terms']:raise ValueError('complete supplied instrument type/terms required')
    baseline=[x for x in books if x.get('role')=='baseline']
    if len(baseline)!=1 or len(books)<2:raise ValueError('one baseline and at least one human-defined hedged book required')
    for book in books:
        require_sources(doc,[book.get('source_ref')])
        if book.get('role') not in {'baseline','hedged'}:raise ValueError('book role unsupported')
        positions=rows(book,'positions','instrument_id')
        for position in positions:
            if position['instrument_id'] not in instrument_ids:raise ValueError('unknown derivative instrument')
            if not text(position.get('quantity_unit')):raise ValueError('position quantity unit required')
            D(position.get('quantity'))
    if 'base' not in {x['scenario_id'] for x in scenarios} or len(scenarios)<2:raise ValueError('base plus at least one supplied stress scenario required')
    for scenario in scenarios:
        require_sources(doc,[scenario.get('source_ref')])
        if not text(scenario.get('version')) or not isinstance(scenario.get('shocks'),dict):raise ValueError('versioned explicit scenario shocks required')
        if scenario['scenario_id']=='base' and scenario['shocks']:raise ValueError('base scenario must have no shocks')
        if scenario['scenario_id']!='base' and not scenario['shocks']:raise ValueError('stress scenario must state shocks')
        for shock in scenario['shocks'].values():
            if not isinstance(shock,dict) or not text(shock.get('unit')):raise ValueError('each supplied shock requires a unit and finite value')
            D(shock.get('value'))
    measure_map={x['measure_id']:x for x in measures}
    if 'pv' not in measure_map or measure_map['pv'].get('unit')!=doc['currency']:raise ValueError('pv measure must use exact review currency')
    for measure in measures:
        require_sources(doc,[measure.get('source_ref')])
        if not text(measure.get('unit')) or not text(measure.get('definition')):raise ValueError('sensitivity units and definition required')
    expected={book['book_id']+'|'+scenario['scenario_id']+'|'+measure['measure_id']:measure['unit'] for book in books for scenario in scenarios for measure in measures}
    supplied=request.get('expected_metrics')
    if not isinstance(supplied,list) or len(supplied)!=len(expected) or {x.get('id'):x.get('unit') for x in supplied if isinstance(x,dict)}!=expected:raise ValueError('engine inventory must cover every book/scenario/measure exactly')
    candidates={x['book_id'] for x in books if x['role']=='hedged'}
    if {x['book_id'] for x in costs}!=candidates:raise ValueError('one supplied cost per human-defined hedged book required')
    cost_map={}
    horizons=set()
    for cost in costs:
        require_sources(doc,[cost.get('source_ref')])
        if cost.get('currency')!=doc['currency'] or not text(cost.get('horizon')) or cost.get('basis')!='one-time-cash-cost':raise ValueError('candidate costs require same currency, explicit horizon and one-time cash basis')
        amount=D(cost.get('amount'))
        if amount<0:raise ValueError('candidate cost cannot be negative')
        cost_map[cost['book_id']]=amount;horizons.add(cost['horizon'])
    if len(horizons)!=1:raise ValueError('candidate cost horizons differ')
    engine=review_engine(doc,request,doc.get('engine_result'),doc.get('independent_benchmark'))
    issues=list(engine['issues']);comparison=[]
    if engine['values'] is not None:
        values={x['id']:D(x['value']) for x in engine['values']};base_id=baseline[0]['book_id']
        for book in books:
            if book['role']=='baseline':continue
            book_id=book['book_id'];cost=cost_map[book_id];scenarios_out=[]
            for scenario in scenarios:
                sid=scenario['scenario_id'];unhedged=values[base_id+'|'+sid+'|pv']-values[base_id+'|base|pv'];hedged=values[book_id+'|'+sid+'|pv']-values[book_id+'|base|pv']
                scenarios_out.append({'scenario_id':sid,'baseline_pnl':str(unhedged),'hedged_book_pnl_before_cost':str(hedged),'incremental_pnl_before_cost':str(hedged-unhedged),'hedged_book_pnl_after_supplied_cost':str(hedged-cost)})
            comparison.append({'book_id':book_id,'supplied_cost':str(cost),'cost_horizon':next(iter(horizons)),'scenarios':scenarios_out})
    out=finish(doc,'portfolio-hedge-reviewer','supplied-full-repricing-challenge-v1',{'engine_review':engine,'comparison':comparison,'hedge_selection':None,'trade_authorized':False},issues,limitations+[
        'Complex prices, Greeks and combined-book scenarios come only from the supplied version-pinned engine and separately supplied benchmark; no engine or local fallback pricer is run.',
        'Scenario P&L is the difference between supplied stressed and base PV for each full book. It is not a linear sensitivity approximation or sum of standalone hedge values.',
        'Cost adjustment subtracts a supplied one-time cash cost, with no inference of premium, funding, XVA, tax or collateral effects already included in model PV.',
        'Matching benchmark and metric inventory does not authenticate model acceptance, benchmark independence, calibration, complete book coverage or financial source truth.',
        'Neutral candidate comparison only; no hedge ranking, recommendation, sizing, order staging or execution.'
    ],['portfolio-stress-test-runner','investment-committee-memo-builder'])
    out['extension']=EXTENSION
    return out

def validate(doc):
    try:compute(doc);return []
    except (ValueError,TypeError,KeyError,ArithmeticError) as exc:return [str(exc)]
