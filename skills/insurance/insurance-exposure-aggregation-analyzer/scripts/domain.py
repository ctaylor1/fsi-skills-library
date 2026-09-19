"""Currency-separated insured schedule TIV; peril slices are not additive."""
from collections import defaultdict
from decimal import Decimal

from insurance_foundation import number
from local_review import Review, shape, text

SKILL = 'insurance-exposure-aggregation-analyzer'
METHOD = 'policy-location-tiv-v1'


def validate(doc):
    return shape(doc, objects=('profile',), lists=('locations',), numbers=('latitude', 'longitude'), nonnegative=('tiv',))


def evaluate(doc):
    d, r = doc['data'], Review(doc)
    r.profile(METHOD)
    r.check(d.get('inventory_complete') is True and 'locations' in d, 'inventory-completeness', 'A supplied complete policy-location inventory is required for totals.')
    rows, seen, identities, quality = d.get('locations', []), set(), set(), []
    totals, accounts, locations, perils = defaultdict(Decimal), defaultdict(Decimal), defaultdict(Decimal), defaultdict(Decimal)
    for row in rows:
        rid = row.get('row_id')
        identity = (row.get('policy_id'), row.get('location_id'))
        valid = r.bind(row, 'location', currency=False)
        valid &= r.check(text(rid) and rid not in seen and all(text(v) for v in identity) and identity not in identities, 'duplicate-location-identity', 'Require unique row and policy/location identity; do not sum duplicated schedule records or automatically deduplicate.', row)
        seen.add(rid)
        identities.add(identity)
        value, currency = number(row.get('tiv')), row.get('currency')
        valid &= r.check(value is not None and text(currency) and text(row.get('account_id')), 'location-value', 'TIV, currency and account must be known.', row)
        covered = row.get('perils', [])
        valid &= r.check(bool(covered) and len(covered) == len(set(covered)) and all(text(p) for p in covered), 'peril-identity', 'Supply unique explicit covered perils; an unknown peril is not zero exposure.', row)
        q = []
        lat, lon = number(row.get('latitude')), number(row.get('longitude'))
        if lat is None or lon is None or not -90 <= lat <= 90 or not -180 <= lon <= 180 or row.get('geocode_quality') not in {'rooftop', 'street'}:
            q.append('geocode requires review')
        if row.get('model_quality') != 'accepted' or not text(row.get('model_version')):
            q.append('model suitability or version unresolved')
        if q:
            r.add('model-data-quality', f'{rid}: ' + '; '.join(q) + '; known schedule TIV remains distinct from modeled loss.', row, block=False)
        quality.append({'row_id': rid, 'geocode_quality': row.get('geocode_quality'), 'model_quality': row.get('model_quality'), 'model_version': row.get('model_version'), 'issues': q})
        if valid:
            totals[currency] += value
            accounts[(currency, row['account_id'])] += value
            locations[(currency, row['location_id'])] += value
            for peril in covered:
                perils[(currency, peril)] += value
    def groups(mapping, field):
        return [{'currency': currency, field: key, 'tiv': value} for (currency, key), value in sorted(mapping.items())]
    # A quality gap does not invalidate supplied TIV. Identity/basis/source gaps do.
    return r.result({'tiv_by_currency': dict(sorted(totals.items())) if not r.blocked else None,
                     'account_tiv': groups(accounts, 'account_id') if not r.blocked else None,
                     'location_tiv': groups(locations, 'location_id') if not r.blocked else None,
                     'peril_tiv': groups(perils, 'peril') if not r.blocked else None,
                     'quality_register': quality, 'record_count': len(rows),
                     'valuation_date': d.get('valuation_date'), 'basis': d.get('basis'),
                     'total_semantics': 'insured schedule TIV across unique policy/location records; not unique physical asset value',
                     'peril_slices_additive': False, 'loss_estimate': None,
                     'underwriting_or_model_acceptance': 'not-determined'})
