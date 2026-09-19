"""Annual joint-sample EP and AAL; event-rate tables establish AAL only."""
from decimal import Decimal

from insurance_foundation import number
from local_review import Review, shape, text

SKILL = 'catastrophe-scenario-analyzer'
METHODS = {'annual-joint-sample-v1', 'event-rate-aal-v1'}


def validate(doc):
    errors = shape(doc, objects=('profile',), lists=('years', 'events'), nonnegative=('weight', 'loss', 'annual_rate'))
    if 'thresholds' in doc.get('data', {}):
        thresholds = doc['data']['thresholds']
        if not isinstance(thresholds, list):
            errors.append('thresholds must be a list')
        else:
            for item in thresholds:
                try:
                    if number(item) is None or number(item) < 0:
                        errors.append('thresholds must be known nonnegative finite amounts')
                except ValueError as exc:
                    errors.append(str(exc))
    return errors


def evaluate(doc):
    d, r = doc['data'], Review(doc)
    method = d.get('method')
    r.profile(method if method in METHODS else 'unsupported')
    r.check(method in METHODS, 'unsupported-method', 'Supply a joint annual sample or annual event-rate catalog; marginal PML summaries cannot establish portfolio EP.')
    r.check(text(d.get('currency')) and text(d.get('model_id')) and text(d.get('model_version')), 'model-scope', 'Preserve currency, model identity and version.')
    r.check(d.get('events_complete') is True and 'events' in d, 'event-completeness', 'Declare an explicit complete event loss table, including zero-event years in annual mode.')
    thresholds = [number(v) for v in d.get('thresholds', [])]
    r.check(len(set(thresholds)) == len(thresholds), 'threshold-identity', 'Threshold amounts must be unique.')
    annual, by_year, event_seen = [], {}, set()
    aal, occurrence_mean, ep = None, None, None
    if method == 'annual-joint-sample-v1':
        r.check(d.get('joint_distribution_supplied') is True and d.get('years_complete') is True and bool(d.get('years')), 'annual-distribution', 'Annual EP requires supplied complete joint annual states with normalized weights; do not assume event independence or silently normalize weights.')
        for row in d.get('years', []):
            yid, weight = row.get('year_id'), number(row.get('weight'))
            r.bind(row, 'year')
            r.check(text(yid) and yid not in by_year and weight is not None and weight > 0, 'year-identity-weight', 'Year-state IDs must be unique with strictly positive supplied probability weights.', row)
            by_year[yid] = {'weight': weight, 'occurrences': {}}
        r.check(all(y['weight'] is not None for y in by_year.values()) and sum((y['weight'] or Decimal(0) for y in by_year.values()), Decimal(0)) == 1, 'weight-mass', 'Annual state probability weights must sum exactly to one, including zero-loss states.')
        for row in d.get('events', []):
            r.bind(row, 'event')
            eid, yid, oid, loss = row.get('event_id'), row.get('year_id'), row.get('occurrence_id'), number(row.get('loss'))
            r.check(text(eid) and (yid, eid) not in event_seen and text(oid) and yid in by_year and loss is not None, 'event-identity', 'Each event row must uniquely bind a known year, occurrence and finite loss; repeated occurrence components aggregate before the annual maximum.', row)
            event_seen.add((yid, eid))
            if yid in by_year and text(oid) and loss is not None:
                occ = by_year[yid]['occurrences']
                occ[oid] = occ.get(oid, Decimal(0)) + loss
        if not r.blocked:
            for yid, year in sorted(by_year.items()):
                losses = list(year['occurrences'].values())
                annual.append({'year_id': yid, 'weight': year['weight'], 'aggregate_loss': sum(losses, Decimal(0)), 'occurrence_loss': max(losses, default=Decimal(0))})
            aal = sum((y['weight'] * y['aggregate_loss'] for y in annual), Decimal(0))
            occurrence_mean = sum((y['weight'] * y['occurrence_loss'] for y in annual), Decimal(0))
            ep = [{'threshold': t,
                   'aggregate_exceedance_probability': sum((y['weight'] for y in annual if y['aggregate_loss'] > t), Decimal(0)),
                   'occurrence_exceedance_probability': sum((y['weight'] for y in annual if y['occurrence_loss'] > t), Decimal(0))} for t in sorted(thresholds)]
    elif method == 'event-rate-aal-v1':
        r.check(d.get('rate_semantics') == 'expected-occurrences-per-year' and d.get('loss_semantics') == 'expected-additive-loss-per-occurrence', 'rate-semantics', 'AAL uses expected annual counts times expected additive event loss; annual probabilities, deterministic return periods and marginal PML are not rates.')
        contributions = []
        for row in d.get('events', []):
            r.bind(row, 'event')
            eid, rate, loss = row.get('event_id'), number(row.get('annual_rate')), number(row.get('loss'))
            r.check(text(eid) and eid not in event_seen and rate is not None and loss is not None, 'event-rate-identity', 'Event-rate catalog requires unique event identities and known loss/rate.', row)
            event_seen.add(eid)
            if rate is not None and loss is not None:
                contributions.append(rate * loss)
        if not r.blocked:
            aal = sum(contributions, Decimal(0))
        r.add('ep-joint-distribution-unavailable', 'Annual event rates justify additive AAL only. Occurrence and aggregate EP require a reviewed annual joint distribution.', block=False, severity='info')
    return r.result({'method': method, 'annual_states': annual if not r.blocked and method == 'annual-joint-sample-v1' else None,
                     'aggregate_aal': aal if not r.blocked else None, 'mean_annual_max_occurrence_loss': occurrence_mean,
                     'exceedance_probabilities': ep, 'exceedance_convention': 'strictly-greater-than-threshold',
                     'currency': d.get('currency'), 'basis': d.get('basis'),
                     'model_id': d.get('model_id'), 'model_version': d.get('model_version'),
                     'pml_sum': None, 'modeled_loss_authentication': 'supplied-not-validated', 'model_approval': 'not-determined'})
