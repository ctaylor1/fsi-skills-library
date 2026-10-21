"""Explicit single-period specialist decompositions and chronological linking (MIT)."""
from decimal import Decimal
from datetime import timedelta
import re
from foundation_contract import D, exact, finish, require_sources, date_value, validate_actual_date, validate_common, text
from specialist_contract import validate_specialist_common as validate_common
from specialist_contract import review_engine

EXTENSION = 'specialist-attribution'


def rows(doc, key, owner=None):
    values = (owner or doc).get(key)
    if not isinstance(values, list) or not values or len(values) > 10000 or any(not isinstance(v, dict) for v in values):
        raise ValueError(key + ' requires a bounded nonempty list')
    ids = [v.get('id') for v in values]
    if any(not text(v) for v in ids) or len(set(ids)) != len(ids):
        raise ValueError('unique identities required for ' + key)
    for row in values: require_sources(doc, [row.get('source_ref')])
    return values


def weight(value):
    result = D(value)
    if not 0 <= result <= 1: raise ValueError('supported beginning weights must be 0..1')
    return result


def ret(value):
    result = D(value)
    if result < -1: raise ValueError('unlevered simple return cannot be below -100%')
    return result


@exact
def compute(doc):
    errors = validate_common(doc)
    if errors: raise ValueError('; '.join(errors))
    if doc.get('extension') != EXTENSION: raise ValueError('unsupported attribution extension')
    mode = doc.get('method')
    require_sources(doc, [doc.get('method_source_ref')])
    if doc.get('return_unit') != 'decimal' or doc.get('basis') not in {'gross-of-fees', 'net-of-fees'}:
        raise ValueError('explicit common decimal-return and fee basis required')
    start, end = date_value(doc.get('period_start')), date_value(doc.get('period_end'))
    if start > end or end > date_value(doc['as_of']): raise ValueError('invalid observed attribution period')
    validate_actual_date(doc, doc['period_end'], doc['method_source_ref'])
    tolerance = D(doc.get('tolerance'))
    if tolerance < 0: raise ValueError('nonnegative reviewed tolerance required')
    issues, effects, details = [], {}, []
    if mode == 'engine':
        engine = review_engine(doc, doc.get('engine_request'), doc.get('engine_record'), doc.get('benchmark'))
        expected = {k:doc[k] for k in ('period_start','period_end','basis','return_unit')}
        if doc['engine_request']['purpose'] != 'specialist-attribution' or doc['engine_request']['input'].get('attribution_context') != expected:
            raise ValueError('engine purpose/period/basis differs from attribution context')
        return finish(doc, 'portfolio-performance-attributor', 'supplied-specialist-attribution-engine-v1',
                      {'engine_review': engine, 'performance_certified': False}, engine['issues'],
                      ['Supplied engine and benchmark challenge only; no risk model, curve or full repricer is invoked.'])
    if mode in {'currency', 'fixed-income'}:
        data = rows(doc, 'segments')
        if sum((weight(x['portfolio_weight']) for x in data), Decimal(0)) != 1 or sum((weight(x['benchmark_weight']) for x in data), Decimal(0)) != 1:
            raise ValueError('complete portfolio and benchmark beginning-weight inventories must each sum exactly to1')
        rp = rb = Decimal(0)
        for row in data:
            wp, wb = weight(row['portfolio_weight']), weight(row['benchmark_weight'])
            if row.get('period_start') != doc['period_start'] or row.get('period_end') != doc['period_end']:
                raise ValueError('segment period differs from review')
            validate_actual_date(doc, row['period_end'], row['source_ref'])
            if mode == 'currency':
                if doc['currency']=='not-applicable' or row.get('fx_convention') != 'base-per-local' or not isinstance(row.get('local_currency'),str) or not re.fullmatch(r'[A-Z]{3}',row['local_currency']):
                    raise ValueError('explicit base-per-local FX convention required')
                lp, lb, fx = ret(row['portfolio_local_return']), ret(row['benchmark_local_return']), ret(row['fx_return'])
                if row['local_currency']==doc['currency'] and fx!=0:
                    raise ValueError('same-currency FX return must be zero')
                components = {'local': wp*lp-wb*lb, 'currency': (wp-wb)*fx, 'local_currency_interaction': wp*lp*fx-wb*lb*fx}
                rp += wp*((1+lp)*(1+fx)-1); rb += wb*((1+lb)*(1+fx)-1)
            else:
                if row.get('currency') != doc['currency'] or row.get('yield_unit') != 'decimal' or row.get('curve_method') != 'parallel-duration-convexity':
                    raise ValueError('same-currency explicit parallel duration/convexity method required')
                dy, ds = D(row['yield_change']), D(row['spread_change'])
                components = {}
                for prefix, w in [('portfolio', wp), ('benchmark', -wb)]:
                    duration, spread_duration, convexity = (D(row[prefix+'_'+k]) for k in ('duration', 'spread_duration', 'convexity'))
                    if duration < 0 or spread_duration < 0: raise ValueError('negative durations outside bounded fixed-income method')
                    parts = {'carry': D(row[prefix+'_carry']), 'rolldown': D(row[prefix+'_rolldown']),
                             'yield': -duration*dy, 'spread': -spread_duration*ds, 'yield_convexity': convexity*dy*dy/2}
                    for key, value in parts.items(): components[key] = components.get(key, Decimal(0)) + w*value
                rp += wp*ret(row['portfolio_realized_return']); rb += wb*ret(row['benchmark_realized_return'])
            for key, value in components.items(): effects[key] = effects.get(key, Decimal(0)) + value
            details.append({'id': row['id'], 'effects': {k:str(v) for k,v in components.items()}, 'source_ref':row['source_ref']})
        if mode == 'currency':
            require_sources(doc, [doc.get('hedge_source_ref')])
            validate_actual_date(doc, doc['period_end'], doc['hedge_source_ref'])
            hp, hb = D(doc['portfolio_hedge_contribution']), D(doc['benchmark_hedge_contribution'])
            effects['supplied_hedge'] = hp-hb; rp += hp; rb += hb
    elif mode == 'factor':
        require_sources(doc, [doc.get('returns_source_ref')])
        validate_actual_date(doc, doc['period_end'], doc['returns_source_ref'])
        if not text(doc.get('risk_model_id')) or not text(doc.get('risk_model_version')) or doc['risk_model_version'].lower() in {'latest','unknown'}:
            raise ValueError('supplied factor risk model must be identified and versioned')
        rp, rb = ret(doc['portfolio_return']), ret(doc['benchmark_return'])
        for row in rows(doc, 'factors'):
            if row.get('exposure_unit') != 'return-per-factor-return' or row.get('return_unit') != 'decimal':
                raise ValueError('factor exposure/return unit mismatch')
            validate_actual_date(doc, doc['period_end'], row['source_ref'])
            contribution = D(row['active_exposure'])*D(row['factor_return'])
            effects[row['id']] = contribution
            details.append({'id':row['id'], 'contribution':str(contribution), 'source_ref':row['source_ref']})
    elif mode == 'linking':
        data = rows(doc, 'periods')
        growth_p = growth_b = Decimal(1); previous_end = None; expected_ids = None
        for row in data:
            a, b = date_value(row['period_start']), date_value(row['period_end'])
            if a > b or a < start or b > end or previous_end is not None and a != previous_end + timedelta(days=1):
                raise ValueError('linking requires ordered, contiguous nonoverlapping observed periods')
            validate_actual_date(doc, row['period_end'], row['source_ref']); previous_end = b
            if not isinstance(row.get('effects'), dict) or not row['effects'] or any(not text(k) for k in row['effects']):
                raise ValueError('each period requires explicit named effect contributions')
            if expected_ids is None: expected_ids = set(row['effects'])
            if set(row['effects']) != expected_ids: raise ValueError('period effect inventories differ')
            p, benchmark_return = ret(row['portfolio_return']), ret(row['benchmark_return'])
            if abs(sum((D(v) for v in row['effects'].values()), Decimal(0))-(p-benchmark_return)) > tolerance:
                issues.append('Period effects do not reconcile: '+row['id'])
            for key,value in row['effects'].items():
                effects[key] = effects.get(key,Decimal(0))*(1+benchmark_return) + D(value)*growth_p
            growth_p *= 1+p; growth_b *= 1+benchmark_return
        if data[0]['period_start'] != doc['period_start'] or data[-1]['period_end'] != doc['period_end']:
            raise ValueError('linked period endpoints differ from review')
        rp, rb = growth_p-1, growth_b-1
    else: raise ValueError('method must be currency/fixed-income/factor/linking/engine')
    active = rp-rb; explained = sum(effects.values(),Decimal(0)); residual = active-explained
    if abs(residual) > tolerance: issues.append('Observed active return contains an unexplained residual above supplied tolerance')
    output = {'method':mode, 'portfolio_return':str(rp), 'benchmark_return':str(rb), 'active_return':str(active),
              'effects':{k:str(v) for k,v in effects.items()}, 'explained_active_return':str(explained), 'residual':str(residual),
              'within_tolerance':abs(residual)<=tolerance, 'details':details, 'performance_certified':False}
    return finish(doc,'portfolio-performance-attributor','specialist-attribution-'+mode+'-v1',output,issues,
                  ['Fixed-income local mode is a parallel duration/convexity approximation, not full repricing; carry/rolldown inputs must not overlap.',
                   'Factor exposures/returns are supplied; no risk model is estimated. Residuals are retained, never redistributed to force reconciliation.',
                   'Currency mode includes the local/FX interaction; supplied hedge contribution is not an independently priced overlay.',
                   'Chronological recursive linking has a declared order and requires a complete supplied period inventory; no GIPS verification.'])
